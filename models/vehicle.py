from abc import ABC, abstractmethod


class Vehicle(ABC):
    def __init__(self, vehicle_id=None, vehicle_number="", owner_name=""):
        self.vehicle_id = vehicle_id
        self.vehicle_number = vehicle_number
        self.owner_name = owner_name

    @abstractmethod
    def calculate_rate(self, rate):
        raise NotImplementedError
