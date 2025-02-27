# Copyright 2020 Open Reaction Database Project Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for ord_schema.units."""

from absl.testing import absltest
from absl.testing import parameterized

from ord_schema import units
from ord_schema.proto import reaction_pb2


class UnitsTest(parameterized.TestCase, absltest.TestCase):
    def setUp(self):
        super().setUp()
        self._resolver = units.UnitResolver()

    @parameterized.named_parameters(
        (
            "capitalized",
            "15.0 ML",
            reaction_pb2.Volume(value=15.0, units=reaction_pb2.Volume.MILLILITER),
        ),
        ("integer", "24 H", reaction_pb2.Time(value=24, units=reaction_pb2.Time.HOUR)),
        (
            "no space",
            "32.1g",
            reaction_pb2.Mass(value=32.1, units=reaction_pb2.Mass.GRAM),
        ),
        (
            "extra space",
            "   32.1      \t   g  ",
            reaction_pb2.Mass(value=32.1, units=reaction_pb2.Mass.GRAM),
        ),
        (
            "abbreviated",
            "10 min.",
            reaction_pb2.Time(value=10.0, units=reaction_pb2.Time.MINUTE),
        ),
        (
            "negative",
            "-78°C",
            reaction_pb2.Temperature(value=-78.0, units=reaction_pb2.Temperature.CELSIUS),
        ),
        (
            "precision",
            "10±5g",
            reaction_pb2.Mass(value=10, precision=5, units=reaction_pb2.Mass.GRAM),
        ),
        (
            "lengths",
            " 10 meter",
            reaction_pb2.Length(value=10, units=reaction_pb2.Length.METER),
        ),
        (
            "scientific",
            "1.2e-3g",
            reaction_pb2.Mass(value=0.0012, units=reaction_pb2.Mass.GRAM),
        ),
        (
            "nanoliters",
            "0.12 nL",
            reaction_pb2.Volume(value=0.12, units=reaction_pb2.Volume.NANOLITER),
        ),
    )
    def test_resolve(self, string, expected):
        self.assertEqual(self._resolver.resolve(string), expected)

    @parameterized.parameters(
        ("1L", "1 molar", "1 mol"),
        ("3mL", "0.1 molar", "300 micromoles"),
        ("100mL", "0.1 molar", "10 millimoles"),
    )
    def test_compute_solute_quantity(self, volume, concentration, expected_quantity):
        conc_resolver = units.UnitResolver(unit_synonyms=units.CONCENTRATION_UNIT_SYNONYMS)
        self.assertEqual(
            units.compute_solute_quantity(
                volume=self._resolver.resolve(volume),
                concentration=conc_resolver.resolve(concentration),
            ),
            reaction_pb2.Amount(moles=self._resolver.resolve(expected_quantity)),
        )

    @parameterized.named_parameters(
        (
            "integer",
            "1-2 h",
            reaction_pb2.Time(value=1.5, precision=0.5, units=reaction_pb2.Time.HOUR),
        )
    )
    def test_resolve_allow_range(self, string, expected):
        self.assertEqual(self._resolver.resolve(string, allow_range=True), expected)

    @parameterized.named_parameters(
        ("bad units", "1.21 GW", "unrecognized units"),
        (
            "multiple matches",
            "15.0 ML 20.0 L",
            "string does not contain a value with units",
        ),
        ("extra period", "15.0. ML", "string does not contain a value with units"),
        ("ambiguous units", "5.2 m", "ambiguous"),
    )
    def test_resolve_should_fail(self, string, expected_error):
        with self.assertRaisesRegex((KeyError, ValueError), expected_error):
            self._resolver.resolve(string)


if __name__ == "__main__":
    absltest.main()
