import unittest

from runscripts.runner import Simulation


class TestRunner(unittest.TestCase):
    """
    A test case class for the runner module.
    """

    def setUp(self):
        """
        Initializes the TestRunner object.
        """
        self.input_dir = "../test_data/test_input_csv"
        self.validation_dir = "../test_data/test_input_csv/refugee_data"
        self.simsetting_file = "../test_data/simsetting.yml"
    

    def test_missing_input(self):
        """
        Test case for checking if ValueError is raised when input_csv_directory is None.
        """
        with self.assertRaises(ValueError) as context:
            sim = Simulation(None, self.validation_dir, 0 , self.simsetting_file)
            sim.run()

        self.assertIn("input_csv_directory cannot be None", str(context.exception))

    def test_missing_validation(self):
        """
        Test case for checking if ValueError is raised when validation_data_directory is None.
        """
        with self.assertRaises(ValueError) as context:
            sim = Simulation(self.input_dir, None, 0 , self.simsetting_file)
            sim.run()

        self.assertIn("validation_data_directory cannot be None", str(context.exception))

    def test_missing_duration(self):
        """
        Test case for checking if ValueError is raised when duration is None.
        """
        with self.assertRaises(ValueError) as context:
            sim = Simulation(self.input_dir, self.validation_dir, None , self.simsetting_file)
            sim.run()

        self.assertIn("duration cannot be None", str(context.exception))

    def test_notinteger_duration(self):
        """
        Test case for checking if ValueError is raised when duration is not an integer.
        """
        with self.assertRaises(ValueError) as context:
            sim = Simulation(self.input_dir, self.validation_dir, 0.5 , self.simsetting_file)
            sim.run()

        self.assertIn("duration must be an integer", str(context.exception))

    def test_output(self):
        """
        Test case for checking if the output of the simulation is not None.
        """
        sim = Simulation(self.input_dir, self.validation_dir, 0 , self.simsetting_file)
        output = sim.run()

        self.assertIsNotNone(output)

if __name__ == '__main__':
    unittest.main()