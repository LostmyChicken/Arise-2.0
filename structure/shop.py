import json

class Shop:
    def __init__(self):
        self.file_path = 'shop.json'
        self.load_shop_data()

    def load_shop_data(self):
        try:
            with open(self.file_path, 'r') as file:
                self.shop_data = json.load(file)
                # Ensure it's a list
                if not isinstance(self.shop_data, list):
                    self.shop_data = []
        except (FileNotFoundError, json.JSONDecodeError):
            self.shop_data = []
            self.save_shop_data()

    def save_shop_data(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.shop_data, file, indent=4)

    def get_max_id_by_currency(self, currency):
        """Get the maximum ID for a specific currency type."""
        max_id = 0
        for item in self.shop_data:
            if item['currency'] == currency and item['id'] > max_id:
                max_id = item['id']
        return max_id

    def add_item(self, name, item, price, currency, quantity=1):
        """Add an item to the shop with a default quantity of 1 and auto-generated ID based on currency."""
        # Get the next available ID for the given currency
        next_id = self.get_max_id_by_currency(currency) + 1
        
        new_item = {
            'id': next_id,
            'name': name,
            'item': item,
            'price': price,
            'currency': currency,
            'quantity': quantity  # Add quantity
        }
        self.shop_data.append(new_item)
        self.save_shop_data()

    def get_item(self, item_id):
        """Retrieve a specific item by its ID."""
        return next((item for item in self.shop_data if item['id'] == item_id), None)

    def get_all_items(self):
        """Retrieve all items in the shop."""
        return self.shop_data

    def update_item(self, item_id, name=None, item=None, price=None, currency=None, quantity=None):
        """Update an existing item in the shop."""
        for item in self.shop_data:
            if item['id'] == item_id:
                if name:
                    item['name'] = name
                if item:
                    item['item'] = item
                if price:
                    item['price'] = price
                if currency:
                    item['currency'] = currency
                if quantity is not None:
                    item['quantity'] = quantity  # Update quantity
                self.save_shop_data()
                return item
        return None

    def delete_item(self, item_id):
        """Delete an item from the shop by its ID."""
        self.shop_data = [item for item in self.shop_data if item['id'] != item_id]
        self.save_shop_data()

    def decrease_quantity(self, item_id, amount=1):
        """Decrease the quantity of an item when it's purchased."""
        item = self.get_item(item_id)
        if item and item['quantity'] >= amount:
            item['quantity'] -= amount
            self.save_shop_data()
            return True
        return False