from django import forms
from .models import Package, Review


class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ('package_name', 'description', 'destination', 'image', 'duration', 'price', 'start_date', 'end_date', 'is_available')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }



class CustomPackageForm(forms.ModelForm):
    stay_days = forms.ChoiceField(
        choices=[(1, '1'), (3, '3'), (5, '5'), (7, '7'), (8, '8'), (10, '10')],
        widget=forms.RadioSelect,
        label="Total Stay (Days)"
    )
    flight_cost = forms.ChoiceField(
        choices=[(1000, '1k'), (1500, '1.5k'), (2000, '2k'), (5000, '5k'), (10000, '10k'), (50000, '50k')],
        widget=forms.RadioSelect,
        label="Flight (BDT)"
    )
    transport_cost = forms.ChoiceField(
        choices=[(5000, '5k'), (10000, '10k'), (20000, '20k'), (40000, '40k'), (50000, '50k'), (100000, '100k')],
        widget=forms.RadioSelect,
        label="Transport Cost (BDT)"
    )
    match_ticket_cost = forms.ChoiceField(
        choices=[(20000, '20k'), (30000, '30k'), (50000, '50k'), (60000, '60k'), (80000, '80k'), (100000, '100k')],
        widget=forms.RadioSelect,
        label="Match Ticket (BDT)"
    )
    country = forms.CharField(max_length=100, required=True, label="Select Country")
    check_in_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="From")
    check_out_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="To")
    num_guests = forms.IntegerField(min_value=1, initial=1, label="No. of Guests")
    origin = forms.CharField(max_length=3, required=False, label="Flight Origin (e.g., DAC)")
    destination = forms.CharField(max_length=3, required=False, label="Flight Destination (e.g., LHR)")
    hotel_destination = forms.CharField(max_length=100, required=False, label="Hotel Destination")

    class Meta:
        model = Package
        fields = ('package_name', 'description')
        widgets = {
            'package_name': forms.TextInput(attrs={'placeholder': 'Enter package name'}),
            'description': forms.Textarea(attrs={'placeholder': 'Describe your package'}),
        }

    def save(self, commit=True):
        package = super().save(commit=False)
        package.is_custom = True
        package.created_by = self.user  # Set in view
        package.start_date = self.cleaned_data['check_in_date']
        package.end_date = self.cleaned_data['check_out_date']
        package.custom_components = {
            'stay_days': self.cleaned_data['stay_days'],
            'flight_cost': self.cleaned_data['flight_cost'],
            'transport_cost': self.cleaned_data['transport_cost'],
            'match_ticket_cost': self.cleaned_data['match_ticket_cost'],
            'country': self.cleaned_data['country'],
            'num_guests': self.cleaned_data['num_guests'],
            'flight_details': getattr(self, 'flight_details', None),
            'hotel_details': getattr(self, 'hotel_details', None),
        }
        package.price = self.calculate_price()
        if commit:
            package.save()
        return package

    def calculate_price(self):
        price = 0
        price += int(self.cleaned_data['stay_days']) * 1000  # Example: 1000 BDT per day
        price += int(self.cleaned_data['flight_cost'])
        price += int(self.cleaned_data['transport_cost'])
        price += int(self.cleaned_data['match_ticket_cost'])
        price += int(self.cleaned_data['num_guests']) * 5000  # Example: 5000 BDT per guest
        # Add API-driven prices for flights and hotels later
        return price
    

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }