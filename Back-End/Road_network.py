from math import radians , sin , cos, sqrt,atan2








def get_crow_flies_distance(coordinates, goal_coordinates):
        """
        Compute the straight-line (crow-flies) distance between two points using the Haversine formula.

        Input Parameters:
            - coordinates: [latitude, longitude] of the current city.
                           Example: [36.4736, 2.8333]            - goal_coordinates: [latitude, longitude] of the goal cit.
                                Example: [35.6911, -0.6417]

        Output:
            - A float representing the distance in kilometers.

        Example:
            >>> distance = problem.get_crow_flies_distance([36.4736, 2.8333], [35.6911, -0.6417])
            >>> round(distance, 2)
            86.75  # (The actual value depends on the coordinates)
        """
        lat1, lon1 = coordinates
        lat2, lon2 = goal_coordinates

        # Convert degrees to radians
        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = 6371 * c  # Earth's radius in kilometers
        return distance