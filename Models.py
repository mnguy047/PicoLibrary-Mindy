"""
# Models.py
# Data model classes (Customer, Contact, Activity) for the IoT CRM system
# Author: Mindy Nguyen
"""

from Log import *


class Customer:
    """
    Represents a CRM customer and holds its associated contacts and activities.

    Attributes:
    ----------
    id : int
        Unique customer identifier from the CRM API.
    customerName : str
        Customer display name mapped from the API 'customer_name' field.
    contacts : list
        List of Contact objects belonging to this customer.
    activities : list
        List of Activity objects belonging to this customer.

    Examples:
    ---------
    1. cust = Customer(19, "Illumina Biotech")
    2. cust.setContacts([Contact(21, 19, "Eva Jelinek", "CFO")])
    """

    def __init__(self, id, customerName, contacts=None, activities=None):
        """
        Initialize a Customer instance.

        Parameters:
        ----------
        id : int
            Unique customer ID.
        customerName : str
            Customer name.
        contacts : list, optional
            Initial list of Contact objects (default: empty list).
        activities : list, optional
            Initial list of Activity objects (default: empty list).
        """
        self.id = id
        self.customerName = customerName if customerName is not None else ""
        self.contacts = contacts if contacts is not None else []
        self.activities = activities if activities is not None else []

    def setContacts(self, contacts):
        """
        Set the list of Contact objects for this customer.

        Parameters:
        ----------
        contacts : list
            List of Contact objects (or None to set an empty list).

        Examples:
        ---------
        1. cust.setContacts(contact_list)
        """
        self.contacts = contacts if contacts is not None else []

    def setActivities(self, activities):
        """
        Set the list of Activity objects for this customer.

        Parameters:
        ----------
        activities : list
            List of Activity objects (or None to set an empty list).

        Examples:
        ---------
        1. cust.setActivities(activity_list)
        """
        self.activities = activities if activities is not None else []


class Contact:
    """
    Represents a contact person associated with a CRM customer.

    Attributes:
    ----------
    id : int
        Unique contact identifier from the CRM API.
    customerID : int
        ID of the parent customer (supplied from the selected customer, since
        the get_contacts endpoint does not return a customerID field).
    name : str
        Contact full name mapped from the API 'name' field.
    role : str
        Contact role/title mapped from the API 'title' (or 'contact_type') field.

    Examples:
    ---------
    1. c = Contact(21, 19, "Eva Jelinek", "CFO")
    """

    def __init__(self, id, customerID, name, role=""):
        """
        Initialize a Contact instance.

        Parameters:
        ----------
        id : int
            Unique contact ID.
        customerID : int
            Associated customer ID.
        name : str
            Contact name.
        role : str, optional
            Contact title/role (default: "").
        """
        self.id = id
        self.customerID = customerID
        self.name = name if name is not None else ""
        self.role = role if role is not None else ""


class Activity:
    """
    Represents a CRM activity associated with a customer.

    Attributes:
    ----------
    id : int
        Unique activity identifier from the CRM API.
    name : str
        Activity name mapped from the API 'name' field.
    date : str
        Activity date mapped from the API 'activity_date' field.
    description : str
        Activity description mapped from the API 'description' field.

    Examples:
    ---------
    1. a = Activity(1, "Cloud Overview", "", "Outlining cloud benefits")
    """

    def __init__(self, id, name, date="", description=""):
        """
        Initialize an Activity instance.

        Parameters:
        ----------
        id : int
            Unique activity ID.
        name : str
            Activity name.
        date : str, optional
            Activity date string (default: "").
        description : str, optional
            Activity description (default: "").
        """
        self.id = id
        self.name = name if name is not None else ""
        self.date = date if date is not None else ""
        self.description = description if description is not None else ""


if __name__ == "__main__":
    # Self-contained verification of Customer, Contact, and Activity models
    cust = Customer(19, "Illumina Biotech")
    contact = Contact(21, cust.id, "Eva Jelinek", "CFO")
    activity = Activity(1, "Cloud Overview", "", "Cloud architecture review")

    cust.setContacts([contact])
    cust.setActivities([activity])

    assert cust.id == 19
    assert cust.customerName == "Illumina Biotech"
    assert len(cust.contacts) == 1
    assert cust.contacts[0].customerID == 19
    assert cust.contacts[0].role == "CFO"
    assert len(cust.activities) == 1
    assert cust.activities[0].name == "Cloud Overview"

    Log.i(f"Customer: {cust.customerName}, Contacts: {len(cust.contacts)}, Activities: {len(cust.activities)}")
    Log.i("Testing complete - Models verified")
