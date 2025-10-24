from django.core.management.base import BaseCommand
from chat.models import FAQ


class Command(BaseCommand):
    help = 'Populate database with sample FAQs for FedEx-like services'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating FAQs...')

        faqs = [
            # Shipping FAQs
            {
                'question': 'How do I create a shipment?',
                'answer': 'To create a shipment, log in to your account and navigate to "Create Shipment". Fill in the recipient details, pickup and delivery addresses, package weight, and any special instructions. You will receive a tracking number once the shipment is created.',
                'keywords': 'create, shipment, new, send, package',
                'category': 'shipping'
            },
            {
                'question': 'What are the shipping rates?',
                'answer': 'Shipping rates are calculated based on package weight, dimensions, destination, and delivery speed. For an accurate quote, please use our shipping calculator or contact customer service.',
                'keywords': 'cost, price, rate, shipping, fee',
                'category': 'pricing'
            },
            {
                'question': 'What items cannot be shipped?',
                'answer': 'We cannot ship hazardous materials, explosives, flammable liquids, illegal substances, or live animals. Please check our prohibited items list for complete details.',
                'keywords': 'prohibited, restricted, banned, cannot ship, illegal',
                'category': 'shipping'
            },
            {
                'question': 'What is the maximum weight for a package?',
                'answer': 'The maximum weight for a standard package is 1000 kg. For heavier shipments, please contact our freight services team for assistance.',
                'keywords': 'weight, maximum, limit, heavy, kg',
                'category': 'shipping'
            },

            # Tracking FAQs
            {
                'question': 'How do I track my shipment?',
                'answer': 'You can track your shipment by entering your tracking number on our Track Shipment page. You will see real-time updates on your package location and delivery status.',
                'keywords': 'track, tracking, where, locate, find, status',
                'category': 'tracking'
            },
            {
                'question': 'What does each tracking status mean?',
                'answer': 'Pending: Package information received. Accepted: Courier has accepted the shipment. Picked Up: Package picked up from sender. In Transit: Package is on its way to destination. Delivered: Package successfully delivered.',
                'keywords': 'status, pending, accepted, transit, delivered',
                'category': 'tracking'
            },
            {
                'question': 'My tracking number is not working',
                'answer': 'If your tracking number is not working, please wait 24 hours after shipment creation as it may take time to update. If the issue persists, contact customer support with your tracking number.',
                'keywords': 'tracking, not working, invalid, error, number',
                'category': 'tracking'
            },

            # Delivery FAQs
            {
                'question': 'How long does delivery take?',
                'answer': 'Standard delivery takes 3-5 business days. Express delivery takes 1-2 business days. International shipments may take 7-14 business days depending on the destination.',
                'keywords': 'delivery, time, how long, duration, days',
                'category': 'delivery'
            },
            {
                'question': 'Can I change the delivery address?',
                'answer': 'Yes, you can request a delivery address change before the package is out for delivery. Contact customer support with your tracking number and new address. Additional fees may apply.',
                'keywords': 'change, address, delivery, modify, update',
                'category': 'delivery'
            },
            {
                'question': 'What if I miss a delivery?',
                'answer': 'If you miss a delivery, the courier will leave a notice with instructions. You can reschedule delivery or pick up the package from the nearest facility. Packages are held for 5 business days.',
                'keywords': 'missed, delivery, not home, absent, reschedule',
                'category': 'delivery'
            },
            {
                'question': 'Do you deliver on weekends?',
                'answer': 'Yes, we offer weekend delivery for express shipments at an additional cost. Standard shipments are delivered Monday through Friday. Contact support to arrange weekend delivery.',
                'keywords': 'weekend, saturday, sunday, holiday, delivery',
                'category': 'delivery'
            },

            # Pickup FAQs
            {
                'question': 'How do I schedule a pickup?',
                'answer': 'When creating a shipment, you can specify a pickup address and time. Our courier will arrive at the specified location during the pickup window. You can also request pickup through customer support.',
                'keywords': 'pickup, schedule, collect, courier, time',
                'category': 'pickup'
            },
            {
                'question': 'Is pickup service free?',
                'answer': 'Pickup service is free for shipments over a certain value. For smaller shipments, a nominal pickup fee may apply. Check the pricing page for details.',
                'keywords': 'pickup, free, cost, fee, charge',
                'category': 'pickup'
            },
            {
                'question': 'Can I change my pickup time?',
                'answer': 'Yes, you can change your pickup time up to 2 hours before the scheduled pickup window. Contact customer support or use the self-service portal to reschedule.',
                'keywords': 'change, pickup, time, reschedule, modify',
                'category': 'pickup'
            },

            # Refund FAQs
            {
                'question': 'How do I request a refund?',
                'answer': 'To request a refund, contact customer support with your tracking number and reason for refund. Refunds are processed within 7-10 business days after approval.',
                'keywords': 'refund, money back, return, cancel',
                'category': 'refund'
            },
            {
                'question': 'What is your refund policy?',
                'answer': 'We offer full refunds for lost or damaged packages (with insurance). Partial refunds may be issued for delayed deliveries. Cancellation refunds are available if requested before pickup.',
                'keywords': 'refund, policy, lost, damaged, delay',
                'category': 'refund'
            },
            {
                'question': 'How long does a refund take?',
                'answer': 'Refunds are processed within 7-10 business days after approval. The amount will be credited to your original payment method. You will receive an email confirmation once processed.',
                'keywords': 'refund, how long, time, process, duration',
                'category': 'refund'
            },

            # Account FAQs
            {
                'question': 'How do I create an account?',
                'answer': 'Click on "Register" at the top of the page, fill in your details, and verify your email address. Once verified, you can start creating shipments and tracking packages.',
                'keywords': 'account, register, sign up, create, new',
                'category': 'account'
            },
            {
                'question': 'I forgot my password',
                'answer': 'Click on "Forgot Password" on the login page. Enter your email address and follow the instructions sent to your email to reset your password.',
                'keywords': 'password, forgot, reset, login, access',
                'category': 'account'
            },
            {
                'question': 'How do I verify my email?',
                'answer': 'After registration, check your email inbox for a verification link. Click the link to verify your email address. You must verify your email before you can log in.',
                'keywords': 'verify, email, verification, confirm, activation',
                'category': 'account'
            },
            {
                'question': 'Can I update my account information?',
                'answer': 'Yes, log in to your account and go to Profile Settings. You can update your name, email, phone number, and address at any time.',
                'keywords': 'update, change, profile, account, information',
                'category': 'account'
            },

            # General FAQs
            {
                'question': 'How can I contact customer support?',
                'answer': 'You can contact customer support through this chat interface, by phone at 1-800-FEDEX, or by email at support@fedexclone.com. We are available 24/7.',
                'keywords': 'contact, support, help, customer service, phone',
                'category': 'general'
            },
            {
                'question': 'What are your business hours?',
                'answer': 'Our customer support is available 24/7. Standard business hours for pickups and deliveries are Monday to Friday, 9 AM to 6 PM. Weekend services are available for express shipments.',
                'keywords': 'hours, time, open, when, availability',
                'category': 'general'
            },
            {
                'question': 'Do you offer insurance for shipments?',
                'answer': 'Yes, we offer shipment insurance for valuable packages. Insurance covers loss, damage, or theft. The cost is calculated based on the declared value of the package.',
                'keywords': 'insurance, protection, coverage, claim, valuable',
                'category': 'general'
            },
            {
                'question': 'Can I ship internationally?',
                'answer': 'Yes, we offer international shipping to over 200 countries. International shipments may require customs documentation and are subject to destination country regulations.',
                'keywords': 'international, overseas, abroad, foreign, country',
                'category': 'shipping'
            },
        ]

        created_count = 0
        for faq_data in faqs:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults={
                    'answer': faq_data['answer'],
                    'keywords': faq_data['keywords'],
                    'category': faq_data['category'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {faq.question}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {faq.question}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} FAQs'))
        self.stdout.write(self.style.SUCCESS(f'Total FAQs in database: {FAQ.objects.count()}'))
