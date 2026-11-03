import math
import unittest
from signal_demo.sorting import (cases, phase, amplitude, signal, signed_circular,
                                 centred_bin, circular_bin_difference, classification, measure, regime)


class SortingTests(unittest.TestCase):
    def test_centred_bins_match_known_thresholds_and_cycle_wrap(self):
        self.assertEqual([centred_bin(v) for v in (0,.049,.05,.1,.949,.95,1)], [0,0,1,1,9,0,0])
        self.assertEqual(circular_bin_difference(.99,.01),0)
        self.assertEqual(circular_bin_difference(.91,.11),-2)

    def test_circle_sign_orientation_and_antipodal_ties(self):
        self.assertAlmostEqual(signed_circular(.99,.01),-.02)
        self.assertAlmostEqual(signed_circular(.01,.99),.02)
        self.assertEqual(signed_circular(.5,0),.5)
        self.assertEqual(signed_circular(0,.5),-.5)

    def test_pointwise_and_aggregate_thresholds_are_distinct(self):
        self.assertEqual([regime(v) for v in (.1,.1001,.2,.2001)], [0,1,1,2])
        self.assertEqual([classification(v)['index'] for v in (.05,.0501,.15,.1501)], [0,1,1,2])
        self.assertEqual(centred_bin(.049),0)
        self.assertEqual(centred_bin(.051),1)
        self.assertEqual(regime(.002),0)  # Tiny state distance does not guarantee equal bins.

    def test_all_fixture_states_respect_endpoints_and_selected_branches(self):
        for case in cases():
            self.assertAlmostEqual(amplitude(0,case),0)
            self.assertAlmostEqual(amplitude(case.r,case),.5)
            self.assertAlmostEqual(amplitude(1,case),1)
            for i in range(501):
                x=i/500; a=amplitude(x,case)
                self.assertTrue(-1e-12 <= signal(x,case) <= 1+1e-12)
                self.assertTrue(0 <= a <= .5+1e-12 if x<case.r else .5-1e-12<=a<=1)

    def test_known_linear_and_sinusoidal_results(self):
        c=cases()
        self.assertAlmostEqual(measure(c[0],'single',1000)['circular_rmsd'],0)
        self.assertAlmostEqual(measure(c[1],'single',1000)['circular_rmsd'],.4/math.sqrt(3))
        self.assertAlmostEqual(measure(c[1],'dual',1000)['circular_rmsd'],0)
        exact=math.sqrt(5/96-1/(2*math.pi**2))
        for index,method in ((2,'single'),(2,'dual'),(3,'dual')):
            row=measure(c[index],method,4000)
            self.assertAlmostEqual(row['circular_rmsd'],exact,places=7)
            self.assertAlmostEqual(row['maximum_circular_distance'],.05262841558678,places=10)

    def test_finite_extreme_results_and_constructed_limits(self):
        expected=[(.282901632,.5,'single'),(.398077882,.01,'single'),(.435946480,.01,'single'),
                  (.282907459,.35,'dual'),(.371549907,.35,'dual')]
        for case,(value,r,method) in zip(cases()[4:9],expected):
            row=measure(case,method,1000)
            self.assertAlmostEqual(row['circular_rmsd'],value,places=7)
            self.assertLess(row['circular_rmsd'],case.limiting_rms)
            self.assertAlmostEqual(case.r,r)

    def test_empirical_fractions_cover_all_samples_and_converge(self):
        for case in (cases()[1],cases()[3],cases()[8],cases()[9]):
            method=case.methods[0]
            coarse,fine=measure(case,method,10000),measure(case,method,20000)
            for key in ('pointwise_regime_fractions','phase_bin_occupancy','amplitude_bin_occupancy'):
                self.assertAlmostEqual(sum(fine[key]),1)
            self.assertLessEqual(abs(coarse['bin_mismatch_fraction']-fine['bin_mismatch_fraction']),.002)
            self.assertAlmostEqual(coarse['circular_rmsd'],fine['circular_rmsd'],places=6)

    def test_resource_and_domain_errors(self):
        for value in (-.1,math.nan,math.inf):
            with self.assertRaises(ValueError):centred_bin(value)
        for count in (True,1,3.5,100):
            with self.assertRaises(ValueError):centred_bin(0,count)
        with self.assertRaises(ValueError):measure(cases()[0],'single',10**8)
        with self.assertRaises(ValueError):phase(.5,0)


if __name__=='__main__': unittest.main()
