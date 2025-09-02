class PhoneNumber:
    def __init__(self, number: str, country_code: str):
        self.number = number
        self.country_code = country_code

    def __composite_values__(self):
        return self.number, self.country_code

    def __repr__(self):
        return f"{self.country_code} {self.number}"

    def __eq__(self, other):
        return (
            isinstance(other, PhoneNumber)
            and self.number == other.number
            and self.country_code == other.country_code
        )
