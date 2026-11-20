import unittest

from app.services.shops import distance_in_kilometers


class ShopDistanceTests(unittest.TestCase):
    def test_same_coordinates_have_zero_distance(self) -> None:
        self.assertEqual(distance_in_kilometers(39.9206, 32.8541, 39.9206, 32.8541), 0)

    def test_one_degree_of_longitude_at_equator_is_about_111_km(self) -> None:
        distance = distance_in_kilometers(0, 0, 0, 1)
        self.assertAlmostEqual(distance, 111.195, places=2)

    def test_kizilay_seed_shops_are_within_three_kilometers(self) -> None:
        distance = distance_in_kilometers(39.9206132, 32.8540559, 39.9218674, 32.8548316)
        self.assertLess(distance, 0.2)


if __name__ == "__main__":
    unittest.main()
