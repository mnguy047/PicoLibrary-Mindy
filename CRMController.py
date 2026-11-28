"""
# CRMController.py
# Controller class orchestrating the IoT CRM system (Option B) on Raspberry Pi Pico 2 W
# Author: Mindy Nguyen
"""

import time
from Log import *
from Lights import GREEN, RED, YELLOW
from Models import Customer, Contact, Activity


class CRMController:
    """
    Controls the IoT CRM workflow (Option B): connects to Wi-Fi, loads customers
    on startup, and loads contacts and activities on demand when a customer is selected.

    Attributes:
    ----------
    customers : list
        List of Customer objects loaded from the REST API.
    currentIndex : int
        Index of the currently displayed item in the active viewMode.
    preloadAll : bool
        Preload flag from UML design (False for Option B on-demand loading).
    viewMode : str
        Current display mode ("CUSTOMER", "CONTACT", or "ACTIVITY").
    selectedCustomer : Customer
        Currently selected Customer object, or None when browsing customers.

    Examples:
    ---------
    1. controller = CRMController(net, lcd, lights, next_btn, select_btn, ssid, password)
    2. controller.start(False)
    """

    CUSTOMERS_URL = "https://iacademy.oracle.com/ords/ism6106/customer/get_customers"
    CONTACTS_URL = "https://iacademy.oracle.com/ords/ism6106/customer/get_contacts/"
    ACTIVITIES_URL = "https://iacademy.oracle.com/ords/ism6106/customer/get_activities/"

    def __init__(self, net, lcd, lights, nextButton, selectButton, ssid, password=None):
        """
        Initialize the CRMController with PicoLibrary components and Wi-Fi credentials.

        Parameters:
        ----------
        net : Net
            PicoLibrary Net instance for Wi-Fi and REST requests.
        lcd : LCDDisplay
            PicoLibrary LCDDisplay instance (16x2 I2C).
        lights : LightStrip
            PicoLibrary LightStrip instance (8 NeoPixels).
        nextButton : Button
            PicoLibrary Button instance used to cycle through items.
        selectButton : Button
            PicoLibrary Button instance used to select customer / advance view.
        ssid : str
            Wi-Fi network SSID.
        password : str, optional
            Wi-Fi network password (None for open networks).
        """
        self.net = net
        self.lcd = lcd
        self.lights = lights
        self.nextButton = nextButton
        self.selectButton = selectButton
        self.ssid = ssid
        self.password = password

        self.customers = []
        self.currentIndex = 0
        self.preloadAll = False
        self.viewMode = "CUSTOMER"
        self.selectedCustomer = None

        self._customersFailed = False
        self._contactsFailed = False
        self._activitiesFailed = False

    def start(self, preloadAll=False):
        """
        Start the CRM application following Sequence Diagram B (Option B).
        Connects to Wi-Fi, loads customers, displays the first customer,
        and polls the Next and Select buttons without interrupts.

        Parameters:
        ----------
        preloadAll : bool, optional
            Kept for UML compatibility; Option B uses False (default: False).

        Examples:
        ---------
        1. controller.start(False)
        """
        print(f"1: start({preloadAll})")
        self.preloadAll = preloadAll
        if self.preloadAll:
            Log.w("Option B only: details load when a customer is selected.")

        self.lcd.clear()
        self.lcd.showText("Connecting WiFi", 0, 0)

        print("2: connect(ssid, password)")
        try:
            self.net.connect(self.ssid, self.password)
        except Exception as e:
            Log.e(f"Wi-Fi connection failed: {e}")
            print(f"Wi-Fi connection failed: {e}")
            self.lcd.clear()
            self.lcd.showText("WiFi Failed", 0, 0)
            self.lcd.showText("Check secrets", 1, 0)
            self.lights.setColor(RED)
            return

        ip = self.net.getLocalIp()
        print(f"3: connected (IP: {ip})")

        self.lcd.clear()
        self.lcd.showText("Loading...", 0, 0)

        print("4: loadCustomers()")
        self.loadCustomers()

        if not self.customers:
            self.lcd.clear()
            if self._customersFailed:
                print("Failed to load customers from API.")
                self.lcd.showText("Cust Load Err", 0, 0)
            else:
                print("No customers available from API.")
                self.lcd.showText("No Customers", 0, 0)
            self.lcd.showText("Check API/Net", 1, 0)
            self.lights.setColor(RED)
            return

        self.viewMode = "CUSTOMER"
        self.currentIndex = 0
        self.selectedCustomer = None
        self.lights.off()
        self.showCustomer()

        prev_next = False
        prev_select = False

        try:
            while True:
                next_pressed = self.nextButton.isPressed()
                select_pressed = self.selectButton.isPressed()

                if next_pressed and not prev_next:
                    self.nextItem()

                if select_pressed and not prev_select:
                    if self.viewMode == "CUSTOMER":
                        print("9: selectButton.isPressed()")
                        print("10: True")
                        self.selectCustomer()
                    elif self.viewMode == "CONTACT":
                        print("23: selectButton.isPressed()")
                        print("24: True")
                        self.viewMode = "ACTIVITY"
                        self.currentIndex = 0
                        self.showActivity()
                    elif self.viewMode == "ACTIVITY":
                        print("Select pressed -> returning to CUSTOMER view")
                        self.viewMode = "CUSTOMER"
                        if self.selectedCustomer in self.customers:
                            self.currentIndex = self.customers.index(self.selectedCustomer)
                        else:
                            self.currentIndex = 0
                        self.lights.off()
                        self.showCustomer()

                prev_next = next_pressed
                prev_select = select_pressed
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("CRM system stopped.")
            self.lights.off()
            self.lcd.clear()

    def loadCustomers(self):
        """
        Retrieve all customers from the get_customers REST endpoint and populate
        self.customers with Customer objects. Requests a larger limit first and
        follows Oracle ORDS pagination links if more pages remain.

        Examples:
        ---------
        1. controller.loadCustomers()
        """
        self.customers = []
        self._customersFailed = False
        url = self.CUSTOMERS_URL + "?limit=100"

        while url:
            print("5: getJson(customersURL)")
            data = self.net.getJson(url)

            if not (isinstance(data, dict) and isinstance(data.get("items"), list)):
                self._customersFailed = True
                print("6: customers request failed")
                return

            for item in data["items"]:
                cust_id = item.get("id")
                cust_name = item.get("customer_name") or "Unnamed"
                if cust_id is not None:
                    self.customers.append(Customer(cust_id, cust_name))

            url = None
            if data.get("hasMore") and isinstance(data.get("links"), list):
                for link in data["links"]:
                    if isinstance(link, dict) and link.get("rel") == "next":
                        url = link.get("href")
                        break

        print(f"6: customersJson ({len(self.customers)} customers)")

    def loadDetails(self, customerID):
        """
        Retrieve contacts and activities for the specified customerID from the
        REST endpoints and store them on self.selectedCustomer.

        Parameters:
        ----------
        customerID : int
            ID of the selected customer.

        Examples:
        ---------
        1. controller.loadDetails(19)
        """
        if self.selectedCustomer is None:
            return

        print(f"12: loadDetails({customerID})")
        self._contactsFailed = False
        self._activitiesFailed = False

        # Load contacts for this customer
        contacts_url = self.CONTACTS_URL + str(customerID)
        print("13: getJson(contactsURL)")
        contacts_data = self.net.getJson(contacts_url)
        if isinstance(contacts_data, dict) and isinstance(contacts_data.get("items"), list):
            contacts = []
            for item in contacts_data["items"]:
                c_id = item.get("id")
                c_name = item.get("name") or "Unnamed"
                c_role = item.get("title") or item.get("contact_type") or ""
                contacts.append(Contact(c_id, customerID, c_name, c_role))
            print(f"14: contactsJson ({len(contacts)} contacts)")
            print("15: setContacts(contacts)")
            self.selectedCustomer.setContacts(contacts)
        else:
            self._contactsFailed = True
            self.selectedCustomer.setContacts([])
            print("14: contacts request failed")

        # Load activities for this customer
        activities_url = self.ACTIVITIES_URL + str(customerID)
        print("16: getJson(activitiesURL)")
        activities_data = self.net.getJson(activities_url)
        if isinstance(activities_data, dict) and isinstance(activities_data.get("items"), list):
            activities = []
            for item in activities_data["items"]:
                a_id = item.get("id")
                a_name = item.get("name") or "Unnamed"
                a_date = item.get("activity_date") or ""
                a_desc = item.get("description") or ""
                activities.append(Activity(a_id, a_name, a_date, a_desc))
            print(f"17: activitiesJson ({len(activities)} activities)")
            print("18: setActivities(activities)")
            self.selectedCustomer.setActivities(activities)
        else:
            self._activitiesFailed = True
            self.selectedCustomer.setActivities([])
            print("17: activities request failed")

    def nextItem(self):
        """
        Advance to the next customer, contact, or activity depending on viewMode
        and refresh the LCD display.

        Examples:
        ---------
        1. controller.nextItem()
        """
        if self.viewMode == "CUSTOMER":
            if not self.customers:
                return
            self.currentIndex = (self.currentIndex + 1) % len(self.customers)
            print(f"Next -> customer {self.currentIndex + 1}/{len(self.customers)}")
            self.showCustomer()
        elif self.viewMode == "CONTACT":
            if self.selectedCustomer is None or not self.selectedCustomer.contacts:
                self.showContact()
                return
            contacts = self.selectedCustomer.contacts
            self.currentIndex = (self.currentIndex + 1) % len(contacts)
            print(f"Next -> contact {self.currentIndex + 1}/{len(contacts)}")
            self.showContact()
        elif self.viewMode == "ACTIVITY":
            if self.selectedCustomer is None or not self.selectedCustomer.activities:
                self.showActivity()
                return
            activities = self.selectedCustomer.activities
            self.currentIndex = (self.currentIndex + 1) % len(activities)
            print(f"Next -> activity {self.currentIndex + 1}/{len(activities)}")
            self.showActivity()

    def selectCustomer(self):
        """
        Select the current customer, fetch its contacts and activities via
        loadDetails(), display the first contact, and update the NeoPixel LEDs.

        Examples:
        ---------
        1. controller.selectCustomer()
        """
        if not self.customers:
            return

        print("11: selectCustomer()")
        self.selectedCustomer = self.customers[self.currentIndex]

        self.lcd.clear()
        self.lcd.showText(self.selectedCustomer.customerName[:16], 0, 0)
        self.lcd.showText("Loading...", 1, 0)

        self.loadDetails(self.selectedCustomer.id)
        self.viewMode = "CONTACT"
        self.currentIndex = 0
        self.showContact()
        self.updateLEDs()

    def showCustomer(self):
        """
        Display the current customer name on row 0 of the LCD and position
        counter on row 1.

        Examples:
        ---------
        1. controller.showCustomer()
        """
        if not self.customers:
            return

        customer = self.customers[self.currentIndex]
        print("7: showCustomer()")
        print(f"8: showText({customer.customerName}, 0, 0)")
        self.lcd.clear()
        self.lcd.showText(customer.customerName[:16], 0, 0)
        self.lcd.showText(f"Cust {self.currentIndex + 1}/{len(self.customers)}"[:16], 1, 0)

    def showContact(self):
        """
        Display the current contact of the selected customer on the LCD, or
        a safe message if the contact list is empty.

        Examples:
        ---------
        1. controller.showContact()
        """
        if self.selectedCustomer is None:
            return

        print("19: showContact()")
        self.lcd.clear()
        contacts = self.selectedCustomer.contacts

        if self._contactsFailed:
            print("20: showText(Contacts error, 1, 0)")
            self.lcd.showText(self.selectedCustomer.customerName[:16], 0, 0)
            self.lcd.showText("Contacts error", 1, 0)
            return

        if not contacts:
            print("20: showText(No contacts, 1, 0)")
            self.lcd.showText(self.selectedCustomer.customerName[:16], 0, 0)
            self.lcd.showText("No contacts", 1, 0)
            return

        contact = contacts[self.currentIndex]
        header = f"Ct {self.currentIndex + 1}/{len(contacts)} {contact.role}".strip()
        print(f"20: showText({contact.name}, 1, 0) [{contact.role}]")
        self.lcd.showText(header[:16], 0, 0)
        self.lcd.showText(contact.name[:16], 1, 0)

    def showActivity(self):
        """
        Display the current activity of the selected customer on the LCD, or
        a safe message if the activity list is empty.

        Examples:
        ---------
        1. controller.showActivity()
        """
        if self.selectedCustomer is None:
            return

        print("25: showActivity()")
        self.lcd.clear()
        activities = self.selectedCustomer.activities

        if self._activitiesFailed:
            print("26: showText(Activity error, 1, 0)")
            self.lcd.showText(self.selectedCustomer.customerName[:16], 0, 0)
            self.lcd.showText("Activity error", 1, 0)
            return

        if not activities:
            print("26: showText(No activities, 1, 0)")
            self.lcd.showText(self.selectedCustomer.customerName[:16], 0, 0)
            self.lcd.showText("No activities", 1, 0)
            return

        activity = activities[self.currentIndex]
        header = f"Act {self.currentIndex + 1}/{len(activities)}"
        if activity.date:
            header = f"{header} {activity.date}"
        print(f"26: showText({activity.name}, 1, 0) [{activity.description}]")
        self.lcd.showText(header[:16], 0, 0)
        self.lcd.showText(activity.name[:16], 1, 0)

    def updateLEDs(self):
        """
        Set the 8 NeoPixels to GREEN if the selected customer has at least one
        activity, RED if the customer has zero activities, or YELLOW if the
        activities REST request failed.

        Examples:
        ---------
        1. controller.updateLEDs()
        """
        if self.selectedCustomer is None:
            return

        print("21: updateLEDs()")
        if self._activitiesFailed:
            print("22: setColor(YELLOW) -> activities request failed")
            self.lights.setColor(YELLOW)
        elif len(self.selectedCustomer.activities) > 0:
            print("22: setColor(GREEN)")
            self.lights.setColor(GREEN)
        else:
            print("22: setColor(RED)")
            self.lights.setColor(RED)


if __name__ == "__main__":
    # Offline unit check using lightweight dummy peripherals (does not call live API)
    class _DummyLCD:
        def clear(self):
            pass

        def showText(self, text, row=0, col=0):
            Log.i(f"[TEST LCD row {row}] {text}")

    class _DummyLights:
        def __init__(self):
            self.last_color = None

        def setColor(self, color):
            self.last_color = color
            Log.i(f"[TEST LED] {color}")

        def off(self):
            self.last_color = (0, 0, 0)

    class _DummyButton:
        def isPressed(self):
            return False

    ctrl = CRMController(None, _DummyLCD(), _DummyLights(), _DummyButton(), _DummyButton(), "", None)
    sample = Customer(1, "Test Customer")
    sample.setContacts([Contact(1, 1, "Barry Bruce", "CFO")])
    sample.setActivities([])
    ctrl.customers = [sample]
    ctrl.selectedCustomer = sample
    ctrl.showCustomer()
    ctrl.showContact()
    ctrl.updateLEDs()
    assert ctrl.lights.last_color == RED
    ctrl.showActivity()

    ctrl._activitiesFailed = True
    ctrl.updateLEDs()
    assert ctrl.lights.last_color == YELLOW
    ctrl.showActivity()
    Log.i("Testing complete - CRMController offline checks passed")