from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, TemplateView, FormView, ListView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import json
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm, ShipmentForm, ContactForm
from .models import Shipment, UserProfile, ShipmentStatusNote

# Create your views here.

class HomeView(TemplateView):
    """
    Home page view
    """
    template_name = 'core/home.html'


class CustomLoginView(DjangoLoginView):
    """
    Custom login view
    """
    template_name = 'core/login.html'

    def form_valid(self, form):
        # Get the username (which is actually email) and password from the form
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        # Try to authenticate
        user = authenticate(self.request, username=username, password=password)

        if user is None:
            messages.error(self.request, 'Invalid email or password.')
            return self.form_invalid(form)

        # If authentication successful, proceed with login
        return super().form_valid(form)


class RegisterView(CreateView):
    """
    User registration view with role selection
    """
    form_class = UserRegistrationForm
    template_name = 'core/register.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        # Save user and activate immediately
        user = form.save(commit=False)
        user.is_active = True  # Activate account immediately without email verification

        # Automatically assign 'recipient' role to all frontend signups
        user.role = 'recipient'
        user.is_staff = False
        user.is_superuser = False

        user.save()

        messages.success(
            self.request,
            f'Account created successfully! You can now log in with your credentials.'
        )

        return redirect(reverse_lazy('login'))

    def form_invalid(self, form):
        messages.error(
            self.request,
            'There was an error with your registration. Please check the form and try again.'
        )
        return super().form_invalid(form)


class CreateShipmentView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new shipments
    Only accessible by admin and shipper roles
    Returns tracking number on success
    """
    model = Shipment
    form_class = ShipmentForm
    template_name = 'core/create_shipment.html'
    success_url = reverse_lazy('core:shipment_success')

    def test_func(self):
        # Only allow admin and shipper roles
        user = self.request.user
        return user.is_staff or user.role in ['admin', 'shipper']

    def handle_no_permission(self):
        messages.error(
            self.request,
            'Access denied. Only shippers and administrators can create shipments.'
        )
        return redirect('core:home')

    def form_valid(self, form):
        # Set the shipper as the current user
        shipment = form.save(commit=False)
        shipment.shipper = self.request.user

        # Get the assigned courier from form
        courier = form.cleaned_data.get('courier')

        # If courier assigned, update status and send notification
        if courier:
            shipment.courier = courier
            shipment.status = 'accepted'
            shipment.save()

            # Send email notification to courier
            self.send_courier_notification(shipment, courier)

            messages.success(
                self.request,
                f'Shipment created and assigned to {courier.username}! Tracking number: {shipment.tracking_number}'
            )
        else:
            shipment.save()
            messages.success(
                self.request,
                f'Shipment created successfully! Your tracking number is: {shipment.tracking_number}'
            )

        # Store tracking number in session to display on success page
        self.request.session['new_tracking_number'] = shipment.tracking_number

        return redirect(self.success_url)

    def send_courier_notification(self, shipment, courier):
        """Send email notification to assigned courier"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            subject = f'New Shipment Assigned - {shipment.tracking_number}'
            message = f'''
Hello {courier.username},

A new shipment has been assigned to you.

Tracking Number: {shipment.tracking_number}
Pickup Address: {shipment.pickup_address}
Delivery Address: {shipment.delivery_address}
Weight: {shipment.weight} kg
Recipient: {shipment.recipient_name}
Contact: {shipment.recipient_phone}

Please log in to your courier dashboard to view more details and update the shipment status.

Best regards,
Nexpress Team
            '''

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@nexpress.com',
                [courier.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending courier notification: {e}")

    def form_invalid(self, form):
        messages.error(
            self.request,
            'There was an error creating your shipment. Please check the form and try again.'
        )
        return super().form_invalid(form)


class ShipmentSuccessView(LoginRequiredMixin, TemplateView):
    """
    Success page displaying the tracking number after shipment creation
    """
    template_name = 'core/shipment_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get tracking number from session
        tracking_number = self.request.session.get('new_tracking_number', None)

        if tracking_number:
            try:
                shipment = Shipment.objects.get(tracking_number=tracking_number)
                context['shipment'] = shipment
                # Clear the session variable
                del self.request.session['new_tracking_number']
            except Shipment.DoesNotExist:
                pass

        return context


class TrackShipmentView(TemplateView):
    """
    Track shipment by tracking number
    """
    template_name = 'core/track_shipment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tracking_number = kwargs.get('tracking_number')

        try:
            shipment = Shipment.objects.select_related('shipper', 'courier').get(
                tracking_number=tracking_number
            )
            context['shipment'] = shipment
            context['found'] = True
        except Shipment.DoesNotExist:
            context['found'] = False
            context['tracking_number'] = tracking_number

        return context


class TrackFormView(TemplateView):
    """
    Track form page where users can enter tracking number
    """
    template_name = 'core/track_form.html'

    def post(self, request, *args, **kwargs):
        tracking_number = request.POST.get('tracking_number', '').strip().upper()
        if tracking_number:
            return redirect('core:track_shipment', tracking_number=tracking_number)
        else:
            messages.error(request, 'Please enter a valid tracking number.')
            return self.get(request, *args, **kwargs)


class TrackingAPIView(View):
    """
    JSON API endpoint for tracking shipments
    Returns shipment status, timestamps, and location data
    """
    def get(self, request, tracking_number):
        try:
            shipment = Shipment.objects.select_related('shipper', 'courier').get(
                tracking_number=tracking_number.upper()
            )

            # Stubbed location data - would come from real tracking system
            locations = self._get_stub_locations(shipment)

            response_data = {
                'success': True,
                'tracking_number': shipment.tracking_number,
                'status': shipment.status,
                'status_display': shipment.get_status_display(),
                'created_at': shipment.created_at.isoformat(),
                'last_updated': shipment.updated_at.isoformat(),
                'weight': float(shipment.weight),
                'recipient': {
                    'name': shipment.recipient_name,
                    'phone': shipment.recipient_phone or None,
                    'email': shipment.recipient_email or None,
                },
                'addresses': {
                    'pickup': shipment.pickup_address,
                    'delivery': shipment.delivery_address,
                },
                'shipper': {
                    'username': shipment.shipper.username,
                    'email': shipment.shipper.email,
                },
                'courier': {
                    'username': shipment.courier.username if shipment.courier else None,
                    'assigned': shipment.courier is not None,
                } if shipment.courier else None,
                'locations': locations,
                'notes': shipment.notes or None,
            }

            return JsonResponse(response_data, status=200)

        except Shipment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Shipment not found',
                'tracking_number': tracking_number,
                'message': 'No shipment found with this tracking number.'
            }, status=404)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Server error',
                'message': str(e)
            }, status=500)

    def _get_stub_locations(self, shipment):
        """
        Generate stubbed location data based on shipment status
        In production, this would query a real tracking/GPS system
        """
        locations = []

        # Always show origin (pickup location)
        locations.append({
            'timestamp': shipment.created_at.isoformat(),
            'location': 'Origin Facility',
            'city': self._extract_city(shipment.pickup_address),
            'description': 'Package information received',
            'status': 'pending'
        })

        # Add locations based on status
        if shipment.status in ['accepted', 'picked_up', 'in_transit', 'delivered']:
            locations.append({
                'timestamp': shipment.updated_at.isoformat(),
                'location': 'Pickup Location',
                'city': self._extract_city(shipment.pickup_address),
                'description': 'Package accepted by courier',
                'status': 'accepted'
            })

        if shipment.status in ['picked_up', 'in_transit', 'delivered']:
            locations.append({
                'timestamp': shipment.updated_at.isoformat(),
                'location': 'Pickup Location',
                'city': self._extract_city(shipment.pickup_address),
                'description': 'Package picked up',
                'status': 'picked_up'
            })

        if shipment.status in ['in_transit', 'delivered']:
            locations.append({
                'timestamp': shipment.updated_at.isoformat(),
                'location': 'Transit Hub',
                'city': 'Distribution Center',
                'description': 'Package in transit to destination',
                'status': 'in_transit'
            })

        if shipment.status == 'delivered':
            locations.append({
                'timestamp': shipment.updated_at.isoformat(),
                'location': 'Delivery Location',
                'city': self._extract_city(shipment.delivery_address),
                'description': 'Package delivered successfully',
                'status': 'delivered'
            })

        if shipment.status == 'returned':
            locations.append({
                'timestamp': shipment.updated_at.isoformat(),
                'location': 'Return Processing',
                'city': self._extract_city(shipment.pickup_address),
                'description': 'Package returned to sender - new tracking number generated',
                'status': 'returned'
            })

        return locations

    def _extract_city(self, address):
        """
        Stub function to extract city from address
        In production, would use proper address parsing
        """
        lines = address.split(',')
        if len(lines) >= 2:
            return lines[-2].strip()
        return 'Unknown City'


class CourierDashboardView(LoginRequiredMixin, ListView):
    """
    Dashboard for courier users to view and manage shipments
    Shows only shipments assigned to the current courier
    """
    model = Shipment
    template_name = 'core/courier_dashboard.html'
    context_object_name = 'shipments'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # Verify user has courier role
        if not request.user.is_authenticated or request.user.role != 'courier':
            messages.error(request, 'Access denied. Courier role required.')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return only shipments assigned to current courier
        """
        user = self.request.user
        return Shipment.objects.filter(
            courier=user
        ).select_related('shipper', 'courier').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Separate shipments into categories for easier template rendering
        all_shipments = self.get_queryset()
        context['pending_shipments'] = []  # Couriers don't see unassigned shipments
        context['my_shipments'] = all_shipments.exclude(status='delivered')
        context['completed_shipments'] = all_shipments.filter(status='delivered')

        # Add counts for quick stats
        context['active_count'] = all_shipments.exclude(status='delivered').count()
        context['completed_count'] = all_shipments.filter(status='delivered').count()
        context['total_assigned'] = all_shipments.count()

        return context


@method_decorator(csrf_exempt, name='dispatch')
class ShipmentStatusUpdateView(View):
    """
    API endpoint for courier to update shipment status
    POST /api/shipment/<tracking_number>/update/
    Expects JSON: {"action": "accept" | "update", "status": "picked_up" | "in_transit" | "delivered"}
    """

    def post(self, request, tracking_number):
        # Verify user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)

        # Verify user has courier role
        if request.user.role != 'courier':
            return JsonResponse({
                'success': False,
                'error': 'Courier role required'
            }, status=403)

        try:
            # Parse JSON body
            data = json.loads(request.body)
            action = data.get('action')
            new_status = data.get('status')

            # Get shipment
            shipment = get_object_or_404(Shipment, tracking_number=tracking_number.upper())

            # Handle "accept" action - courier accepts pending shipment
            if action == 'accept':
                if shipment.status != 'pending':
                    return JsonResponse({
                        'success': False,
                        'error': 'Only pending shipments can be accepted'
                    }, status=400)

                if shipment.courier is not None:
                    return JsonResponse({
                        'success': False,
                        'error': 'Shipment already assigned to another courier'
                    }, status=400)

                # Assign courier and update status
                shipment.courier = request.user
                shipment.status = 'accepted'
                shipment.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Shipment accepted successfully',
                    'tracking_number': shipment.tracking_number,
                    'status': shipment.status,
                    'status_display': shipment.get_status_display()
                })

            # Handle "update" action - update status of assigned shipment
            elif action == 'update':
                # Verify courier is assigned to this shipment
                if shipment.courier != request.user:
                    return JsonResponse({
                        'success': False,
                        'error': 'You are not assigned to this shipment'
                    }, status=403)

                # Validate status progression
                valid_statuses = ['accepted', 'picked_up', 'in_transit', 'delivered']
                if new_status not in valid_statuses:
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                    }, status=400)

                # Update status
                shipment.status = new_status
                shipment.save()

                return JsonResponse({
                    'success': True,
                    'message': f'Shipment status updated to {shipment.get_status_display()}',
                    'tracking_number': shipment.tracking_number,
                    'status': shipment.status,
                    'status_display': shipment.get_status_display()
                })

            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action. Must be "accept" or "update"'
                }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON in request body'
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Server error',
                'message': str(e)
            }, status=500)


class RecipientDashboardView(LoginRequiredMixin, ListView):
    """
    Dashboard for recipients to track their expected shipments
    Shows shipments where the recipient email matches the user's email
    """
    model = Shipment
    template_name = 'core/recipient_dashboard.html'
    context_object_name = 'shipments'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # Verify user has recipient role
        if not request.user.is_authenticated or request.user.role != 'recipient':
            messages.error(request, 'Access denied. Recipient role required.')
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return shipments where recipient email matches user's email
        """
        user = self.request.user
        return Shipment.objects.filter(
            recipient_email__iexact=user.email
        ).select_related('shipper', 'courier').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Separate shipments by status
        all_shipments = self.get_queryset()
        context['in_transit_shipments'] = all_shipments.filter(
            status__in=['accepted', 'picked_up', 'in_transit']
        )
        context['delivered_shipments'] = all_shipments.filter(status='delivered')
        context['pending_shipments'] = all_shipments.filter(status='pending')

        # Add counts
        context['total_expected'] = all_shipments.count()
        context['in_transit_count'] = context['in_transit_shipments'].count()
        context['delivered_count'] = context['delivered_shipments'].count()

        return context


class ContactView(TemplateView):
    """
    Contact page with a form. Since email isn't configured, submissions are printed to
    the server terminal and also passed to the template so client-side JS can log them.
    """
    template_name = 'core/contact.html'

    def get(self, request, *args, **kwargs):
        form = ContactForm()
        return render(request, self.template_name, {'form': form, 'submitted_json': None})

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        submitted = None
        submitted_json = None
        if form.is_valid():
            submitted = form.cleaned_data
            # Print to server terminal
            print('--- Contact Form Submission ---')
            print(f"Name: {submitted.get('name')}")
            print(f"Email: {submitted.get('email')}")
            print(f"Phone: {submitted.get('phone')}")
            print('Message:')
            print(submitted.get('message'))
            print('--- End Submission ---')

            # Add a success message for the user
            messages.success(request, 'Thank you! Your message has been received. Our team will get back to you soon.')
            # Render the form again (empty) but include submitted data for console logging
            form = ContactForm()
            try:
                submitted_json = json.dumps(submitted)
            except Exception:
                submitted_json = None
        else:
            messages.error(request, 'Please correct the errors in the form.')

        return render(request, self.template_name, {'form': form, 'submitted': submitted, 'submitted_json': submitted_json})



class AdminShipmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Admin view to list and manage all shipments
    """
    model = Shipment
    template_name = 'core/admin_shipment_list.html'
    context_object_name = 'shipments'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == 'admin'

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Admin privileges required.')
        return redirect('core:home')

    def get_queryset(self):
        queryset = Shipment.objects.select_related('shipper', 'courier').order_by('-created_at')

        # Filter by status if provided
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Search by tracking number or recipient name
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(tracking_number__icontains=search_query) |
                Q(recipient_name__icontains=search_query) |
                Q(shipper__username__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Shipment.STATUS_CHOICES
        context['current_status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')

        # Count by status
        context['status_counts'] = {
            status[0]: Shipment.objects.filter(status=status[0]).count()
            for status in Shipment.STATUS_CHOICES
        }

        # Get all couriers for assignment dropdown
        context['couriers'] = UserProfile.objects.filter(role='courier').order_by('username')

        # For JavaScript dropdown population
        context['couriers_json'] = json.dumps([
            {
                'id': courier.id,
                'username': courier.username,
                'email': courier.email
            }
            for courier in context['couriers']
        ])

        return context


class AdminShipmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Admin view to update shipment status and details
    """

    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == 'admin'

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Admin privileges required.')
        return redirect('core:home')

    def post(self, request, tracking_number):
        shipment = get_object_or_404(Shipment, tracking_number=tracking_number.upper())

        # Get form data
        new_status = request.POST.get('status')
        courier_id = request.POST.get('courier')
        hold_reason = request.POST.get('hold_reason', '').strip()
        status_note = request.POST.get('status_note', '').strip()

        # Validate status
        valid_statuses = [choice[0] for choice in Shipment.STATUS_CHOICES]
        if new_status not in valid_statuses:
            messages.error(request, 'Invalid status selected.')
            return redirect('core:admin_shipment_list')

        # Check if status is hold but no reason provided
        if new_status == 'hold' and not hold_reason:
            messages.error(request, 'Hold reason is required when setting status to Hold.')
            return redirect('core:admin_shipment_list')

        # Store old status for notification
        old_status = shipment.status

        # Update status and previous_status
        if old_status != new_status:
            shipment.previous_status = old_status

        shipment.status = new_status

        # Update hold_reason
        if new_status == 'hold':
            shipment.hold_reason = hold_reason
        else:
            # Clear hold_reason if status is not hold
            shipment.hold_reason = None

        # Update courier if provided
        if courier_id:
            try:
                courier = UserProfile.objects.get(id=courier_id, role='courier')
                shipment.courier = courier
            except UserProfile.DoesNotExist:
                messages.error(request, 'Invalid courier selected.')
                return redirect('core:admin_shipment_list')

        shipment.save()

        # Create status note if provided
        if status_note:
            ShipmentStatusNote.objects.create(
                shipment=shipment,
                status=new_status,
                note=status_note,
                created_by=request.user
            )

        # Send email notification if status changed
        if old_status != new_status:
            self.send_status_change_email(shipment, old_status, new_status)

        messages.success(
            request,
            f'Shipment {tracking_number} updated: {dict(Shipment.STATUS_CHOICES)[old_status]} → {dict(Shipment.STATUS_CHOICES)[new_status]}'
        )

        # Redirect back to list or to the specific shipment
        if request.POST.get('redirect') == 'detail':
            return redirect('core:track_shipment', tracking_number=tracking_number)
        else:
            return redirect('core:admin_shipment_list')

    def send_status_change_email(self, shipment, old_status, new_status):
        """Send email notification about status change"""
        # Prepare email recipients
        recipients = []

        # Add shipper email
        if shipment.shipper.email:
            recipients.append(shipment.shipper.email)

        # Add recipient email if provided
        if shipment.recipient_email:
            recipients.append(shipment.recipient_email)

        if not recipients:
            return

        # Prepare email content
        subject = f'Shipment Update - {shipment.tracking_number}'

        old_status_display = dict(Shipment.STATUS_CHOICES).get(old_status, old_status)
        new_status_display = dict(Shipment.STATUS_CHOICES).get(new_status, new_status)

        message = f'''
Hello,

Your shipment status has been updated:

Tracking Number: {shipment.tracking_number}
Previous Status: {old_status_display}
New Status: {new_status_display}
'''

        # Add hold reason if status is hold
        if new_status == 'hold' and shipment.hold_reason:
            message += f'\nReason for Hold: {shipment.hold_reason}\n'

        message += f'''
Package Details:
- From: {shipment.shipper.username}
- To: {shipment.recipient_name}
- Weight: {shipment.weight} kg

You can track your shipment at any time using your tracking number.

Thank you for using our service!

Best regards,
Nexpress Team
        '''

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@nexpress.com',
                recipients,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending status change email: {e}")


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Admin-only dashboard showing shipment statistics and recent activity
    Displays counts by status, user statistics, and recent shipments
    """
    template_name = 'core/admin_dashboard.html'

    def test_func(self):
        # Only allow users with admin role or staff status
        return self.request.user.is_staff or self.request.user.role == 'admin'

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Admin privileges required.')
        return redirect('core:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Shipment counts by status
        status_counts = {}
        for status_code, status_display in Shipment.STATUS_CHOICES:
            status_counts[status_code] = {
                'display': status_display,
                'count': Shipment.objects.filter(status=status_code).count()
            }
        context['status_counts'] = status_counts

        # Total shipments
        context['total_shipments'] = Shipment.objects.count()

        # User statistics
        context['total_users'] = UserProfile.objects.count()
        context['courier_count'] = UserProfile.objects.filter(role='courier').count()
        context['shipper_count'] = UserProfile.objects.filter(role='shipper').count()

        # Recent shipments (last 20)
        context['recent_shipments'] = Shipment.objects.select_related(
            'shipper', 'courier'
        ).order_by('-created_at')[:20]

        # Shipments created today
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        context['today_shipments'] = Shipment.objects.filter(
            created_at__gte=today_start
        ).count()

        # Shipments created this week
        week_start = timezone.now() - timedelta(days=7)
        context['week_shipments'] = Shipment.objects.filter(
            created_at__gte=week_start
        ).count()

        # Unassigned pending shipments
        context['unassigned_count'] = Shipment.objects.filter(
            status='pending',
            courier__isnull=True
        ).count()

        # Active couriers (couriers with at least one active shipment)
        context['active_couriers'] = UserProfile.objects.filter(
            role='courier',
            shipments_assigned__status__in=['accepted', 'picked_up', 'in_transit']
        ).distinct().count()

        # Top shippers (users who have created the most shipments)
        context['top_shippers'] = UserProfile.objects.filter(
            shipments_sent__isnull=False
        ).annotate(
            shipment_count=Count('shipments_sent')
        ).order_by('-shipment_count')[:5]

        # Top couriers (couriers who have delivered the most shipments)
        context['top_couriers'] = UserProfile.objects.filter(
            role='courier',
            shipments_assigned__status='delivered'
        ).annotate(
            delivered_count=Count('shipments_assigned')
        ).order_by('-delivered_count')[:5]

        return context
