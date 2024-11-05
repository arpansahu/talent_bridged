from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import EmailsOtpRecord, ContactSubmission
from .forms import ContactForm 
from django.conf import settings
import base64
import pyotp
import traceback
from mailjet_rest import Client  # Import Mailjet client
from datetime import datetime
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone

# Create your views here.

def contact_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            email = form.cleaned_data.get('email').lower()
            contact = form.cleaned_data.get('contact')
            subject = form.cleaned_data.get('subject')
            message_form = form.cleaned_data.get('message')
            otp = request.POST.get('otp', None)

            # OTP verification
            key = base64.b32encode((email + settings.SECRET_KEY).encode())
            otp_obj = pyotp.TOTP(key, interval=settings.OTP_EXPIRY_TIME)

            if otp_obj.verify(otp):
                try:
                    # Save the data to the ContactSubmission model
                    ContactSubmission.objects.create(
                        name=name,
                        email=email,
                        contact=contact,
                        subject=subject,
                        message=message_form
                    )
                    return JsonResponse({'status': 'success', 'message': 'Your query has been received. We will get back to you soon.'})
                except Exception as e:
                    print(traceback.format_exc())
                    return JsonResponse({'status': 'error', 'message': 'Unable to submit your query. Please try again later.'}, status=500)

            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid OTP. Please try again.'}, status=400)

        else:
            # Extract the error messages from the form and pass them in the response
            errors = form.errors.as_json()
            return JsonResponse({'status': 'error', 'message': 'Invalid form data. Please check your inputs.', 'errors': errors}, status=400)

    return render(request, 'extras/contact.html', {'form': ContactForm()})


@csrf_exempt
def get_otp_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        email = request.POST.get('email', '').lower()
        email_status_obj = EmailsOtpRecord.objects.filter(email=email, date=datetime.today()).first()
        status = None
        message = None
        otp = None
        status_code = None
        subject = 'One Time Password for Contacting on scrapeoptimus.com'

        if email_status_obj and email_status_obj.count >= 5:
            status_code = 400
            status = 'Failed'
            message = 'Same Email address cannot generate more than 5 OTPs in a day'
        else:
            # Generate the OTP using pyotp
            key = base64.b32encode((email + settings.SECRET_KEY).encode())
            otp_obj = pyotp.TOTP(key, interval=settings.OTP_EXPIRY_TIME)
            otp = otp_obj.now()

            # Prepare context for the email template
            context = {
                'otp': otp,
                'name': email.split('@')[0],  # Using the first part of email as a placeholder for the name
                'email': email,
                'date': timezone.now().strftime('%d %b, %Y'),
                'valid_minutes': settings.OTP_EXPIRY_TIME / 60
            }

            # Render the HTML email content using the template
            html_content = render_to_string('emails/otp_email_template.html', context)

            # Email data payload for Mailjet
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": settings.MAIL_JET_VERIFICATION_EMAIL,
                            "Name": "scrapeoptimus.com"
                        },
                        "To": [
                            {
                                "Email": email,
                                "Name": email
                            }
                        ],
                        "Subject": subject,
                        "HTMLPart": html_content,
                        "CustomID": email
                    }
                ]
            }

            try:
                mailjet = Client(auth=(settings.MAIL_JET_API_KEY, settings.MAIL_JET_API_SECRET), version='v3.1')
                result = mailjet.send.create(data=data)
                if result.status_code == 200:
                    status_code = 200
                    status = 'Success'
                    message = 'OTP sent to your email successfully.'

                    # Update or create OTP record
                    if email_status_obj:
                        email_status_obj.count += 1
                        email_status_obj.save()
                    else:
                        EmailsOtpRecord.objects.create(email=email, count=1)

            except Exception as e:
                tb = traceback.format_exc()
                print(tb)
                status_code = 500
                status = 'Error'
                message = 'An error occurred while sending the OTP.'

        # Return JSON response
        return JsonResponse({'status': status, 'message': message}, status=status_code)

    # If the request method is not POST or not an AJAX request
    return JsonResponse({'status': 'Failed', 'message': 'Invalid request'}, status=400)