from django.core.management.base import BaseCommand
from subscriptions.models import Service, ServicePlan, ServiceType, PlanType


class Command(BaseCommand):
    help = 'Create sample services and plans'

    def handle(self, *args, **kwargs):
        # Create TryOn Service
        tryon_service, created = Service.objects.get_or_create(
            service_type=ServiceType.TRYON,
            defaults={
                'name': 'AI Virtual Try-On',
                'description': 'AI-powered garment visualization on models',
                'is_active': True,
                'icon': 'sparkles'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created service: {tryon_service.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Service already exists: {tryon_service.name}'))

        # Create Basic Plan
        basic_plan, created = ServicePlan.objects.get_or_create(
            service=tryon_service,
            plan_type=PlanType.BASIC,
            defaults={
                'name': 'Basic',
                'description': 'Perfect for trying out the service',
                'price_monthly': '9.99',
                'price_yearly': '99.90',
                'usage_limit': 50,
                'features': [
                    '50 try-ons per month',
                    'Standard quality results',
                    'Email support',
                    'History tracking'
                ],
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created plan: {basic_plan.name}'))

        # Create Pro Plan
        pro_plan, created = ServicePlan.objects.get_or_create(
            service=tryon_service,
            plan_type=PlanType.PRO,
            defaults={
                'name': 'Pro',
                'description': 'Best for professionals and businesses',
                'price_monthly': '29.99',
                'price_yearly': '299.90',
                'usage_limit': 500,
                'features': [
                    '500 try-ons per month',
                    'High quality results',
                    'Priority support',
                    'Advanced analytics',
                    'API access',
                    'Batch processing'
                ],
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created plan: {pro_plan.name}'))

        # Create Enterprise Plan
        enterprise_plan, created = ServicePlan.objects.get_or_create(
            service=tryon_service,
            plan_type=PlanType.ENTERPRISE,
            defaults={
                'name': 'Enterprise',
                'description': 'Unlimited access for large organizations',
                'price_monthly': '99.99',
                'price_yearly': '999.90',
                'usage_limit': -1,
                'features': [
                    'Unlimited try-ons',
                    'Premium quality results',
                    '24/7 priority support',
                    'Custom integrations',
                    'Dedicated account manager',
                    'SLA guarantee',
                    'White-label options'
                ],
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created plan: {enterprise_plan.name}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Sample data created successfully!'))
