from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.http import HttpResponse
import uuid
import json

from .models import Payment, PaymentMethod, Invoice, PaymentStatus, PaymentProvider
from .serializers import (
    PaymentSerializer, PaymentMethodSerializer,
    CreatePaymentSerializer, InvoiceSerializer
)


class CreatePaymentView(generics.CreateAPIView):
    serializer_class = CreatePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        validated_data = serializer.validated_data

        payment_id = str(uuid.uuid4())

        payment = Payment.objects.create(
            user=user,
            payment_id=payment_id,
            provider=validated_data['provider'],
            payment_type=validated_data['payment_type'],
            amount=validated_data['amount'],
            currency=validated_data['currency'],
            description=validated_data.get('description', ''),
            subscription_id_id=validated_data.get('subscription_id'),
            workflow_id_id=validated_data.get('workflow_id'),
            status=PaymentStatus.PENDING
        )

        provider = validated_data['provider']

        if provider == PaymentProvider.STRIPE:
            payment_url = self._create_stripe_payment(payment, validated_data)
        elif provider == PaymentProvider.IYZICO:
            payment_url = self._create_iyzico_payment(payment, validated_data)
        elif provider == PaymentProvider.PAYTR:
            payment_url = self._create_paytr_payment(payment, validated_data)
        else:
            return Response({
                'error': 'Unsupported payment provider'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'payment': PaymentSerializer(payment).data,
            'payment_url': payment_url,
            'message': 'Payment created successfully'
        }, status=status.HTTP_201_CREATED)

    def _create_stripe_payment(self, payment, data):
        return f"https://checkout.stripe.com/pay/{payment.payment_id}"

    def _create_iyzico_payment(self, payment, data):
        return f"https://sandbox-api.iyzipay.com/payment/form/{payment.payment_id}"

    def _create_paytr_payment(self, payment, data):
        return f"https://www.paytr.com/odeme/{payment.payment_id}"


class PaymentStatusView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'payment_id'

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, provider, *args, **kwargs):
        if provider == 'stripe':
            return self._handle_stripe_webhook(request)
        elif provider == 'iyzico':
            return self._handle_iyzico_webhook(request)
        elif provider == 'paytr':
            return self._handle_paytr_webhook(request)
        else:
            return Response({'error': 'Unknown provider'}, status=400)

    def _handle_stripe_webhook(self, request):
        payload = request.body
        try:
            data = json.loads(payload)

            if data.get('type') == 'payment_intent.succeeded':
                payment_id = data['data']['object']['metadata'].get('payment_id')
                if payment_id:
                    try:
                        payment = Payment.objects.get(payment_id=payment_id)
                        payment.status = PaymentStatus.COMPLETED
                        payment.provider_payment_id = data['data']['object']['id']
                        payment.provider_response = data
                        payment.save()

                        self._handle_successful_payment(payment)
                    except Payment.DoesNotExist:
                        pass

            return Response({'status': 'success'})
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=400)

    def _handle_iyzico_webhook(self, request):
        return Response({'status': 'success'})

    def _handle_paytr_webhook(self, request):
        return Response({'status': 'success'})

    def _handle_successful_payment(self, payment):
        if payment.payment_type == 'subscription' and payment.subscription_id:
            subscription = payment.subscription_id
            subscription.status = 'active'
            subscription.save()


class PaymentMethodListView(generics.ListCreateAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user, is_active=True)


class InvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'invoice_number'

    def get_queryset(self):
        return Invoice.objects.filter(payment__user=self.request.user)


