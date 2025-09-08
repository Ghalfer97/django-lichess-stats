from django import forms

class LichessForm(forms.Form):
    username = forms.CharField(
        label="Lichess Username",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your Lichess username"})
    )

    gamemode = forms.ChoiceField(
        label="Game Mode",
        choices=[
            ("all","All"),
            ("bullet", "Bullet"),
            ("blitz", "Blitz"),
            ("rapid", "Rapid"),
            ("classical", "Classical"),
        ],
        widget=forms.Select(attrs={"class": "form-control"})
    )

    number_of_games = forms.IntegerField(
        label="Number of Games",
        min_value=1,
        max_value=20000,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 500"})
    )

    opening = forms.CharField(
        label="Opening (optional)",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Sicilian Defense"})
    )

    personal_token = forms.CharField(
        label="Personal Token",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your Lichess Personal Token"})
    )