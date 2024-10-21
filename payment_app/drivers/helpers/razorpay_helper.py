"""Module for drivers's helper functions."""
class RazorpayHelper:
    """Razorpay class to help add details to payment events."""
    def __init__(self):
        """Constructor"""
        self.__data = {}
        self.__notes = {}

    def set_data(self, key: str, value):
        """Add key value: __data"""
        self.__data[key] = value
        return self

    def add_data(self, data: dict):
        """Update data: __data"""
        self.__data = self.__data | data
        return self

    def get_data(self):
        """Return data: __data"""
        return self.__data

    def set_notes(self, key: str, value):
        """Add key value: __notes"""
        self.__notes[key] = value
        return self

    def add_notes(self, notes: dict):
        """Update notes: __notes"""
        self.__notes = self.__notes | notes
        return self

    def get_notes(self) -> dict:
        """Return notes: __notes"""
        return self.__notes
