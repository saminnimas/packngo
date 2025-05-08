from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import Payment  # Adjust import based on your project structure
import json


@login_required
def expense_log(request):
    """Display the user's expense log from past tours."""
    payments = Payment.objects.filter(user=request.user, status='succeeded').select_related('package')
    return render(request, 'packages/expense_log.html', {'payments': payments})


@login_required
def expense_log_visualization(request):
    """Display a visualization of the user's expense log."""
    payments = Payment.objects.filter(user=request.user, status='succeeded').select_related('package')
    # Prepare data for Chart.js
    chart_data = {
        'labels': [payment.package.package_name for payment in payments],
        'amounts': [float(payment.amount) for payment in payments],
        'durations': [payment.package.duration or 0 for payment in payments],  # Use 0 if duration is None
    }
    return render(request, 'packages/expense_log_visualization.html', {
        'chart_data': json.dumps(chart_data),  # Convert to JSON for JavaScript
    })