r"""
Automorphisms of abelian groups

This implements groups of automorphisms of abelian groups.

EXAMPLES::

    sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
    sage: G = AbelianGroupGap([2,6])
    sage: autG = G.aut()

Automorphisms acts on the elements of the domain::

    sage: g = G.an_element()
    sage: f = autG.an_element()
    sage: f
    [ g2^2, g1, g2^3 ] -> [ g2^4, g1*g2^3, g2^3 ]
    sage: (g, f(g))
    (g1*g2, g1*g2^2)

Or anything coercible into its domain::

    sage: A = AbelianGroup([2,6])
    sage: a = A.an_element()
    sage: (a, f(a))
    (f0*f1, g1*g2^2)
    sage: A = AdditiveAbelianGroup([2,6])
    sage: a = A.an_element()
    sage: (a, f(a))
    ((1, 0), g1*g2^3)
    sage: f((1,1))
    g1*g2^2

We can compute conjugacy classes::

    sage: autG.conjugacy_classes_representatives()
    (1,
     [ g2^2, g1, g2^3 ] -> [ g2^2, g2^3, g1 ],
     [ g2^2, g1, g2^3 ] -> [ g2^4, g1*g2^3, g2^3 ],
     [ g2^2, g1, g2^3 ] -> [ g2^4, g2^3, g1*g2^3 ],
     [ g2^2, g1, g2^3 ] -> [ g2^2, g2^3, g1*g2^3 ],
     [ g1, g2^3, g2^2 ] -> [ g1, g2^3, g2^4 ])

the group order::

    sage: autG.order()
    12

or create subgroups and do the same for them::

    sage: S = autG.subgroup(autG.gens()[:1])
    sage: S
    Subgroup of automorphisms of Abelian group with gap, generator orders (2, 6)
    generated by 1 automorphisms

Only automorphism groups of finite abelian groups are supported::

    sage: G = AbelianGroupGap([0,2])        # optional gap_packages
    sage: autG = G.aut()
    Traceback (most recent call last):
    ...
    ValueError: Only finite abelian groups are supported.

AUTHORS:

- Simon Brandhorst (2018-02-17): initial version
"""

# ****************************************************************************
#       Copyright (C) 2013 YOUR NAME <your email>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
# ****************************************************************************
from sage.groups.group import Group
from sage.groups.libgap_wrapper import ParentLibGAP, ElementLibGAP
from sage.groups.libgap_mixin import GroupMixinLibGAP
from sage.libs.gap.element import GapElement
from sage.libs.gap.libgap import libgap
from sage.structure.unique_representation import UniqueRepresentation
from sage.rings.all import ZZ
from sage.matrix.matrix_space import MatrixSpace

class AbelianGroupAutomorphismGroupElement(ElementLibGAP):
    """
    Automorphisms of abelian groups with gap.

    INPUT:

    - ``x`` -- a libgap element.
    - ``parent`` -- the parent :class:`AbelianGroupAutomorphismGroup_generic`

    EXAMPLES::

        sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
        sage: G = AbelianGroupGap([2,3,4,5])
        sage: f = G.aut().an_element()
    """
    def __init__(self, parent, x, check=True):
        """
        The Python constructor.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: f = G.aut().an_element()
            sage: TestSuite(f).run()
        """
        if check:
            if not x in parent.gap():
                raise ValueError("%s is not in the group %s" %(x, parent))
        ElementLibGAP.__init__(self, parent, x)

    def __hash__(self):
        r"""
        The hash of this element.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: f = G.aut().an_element()
            sage: f.__hash__()      # random
        """
        return hash(self.matrix())

    def __reduce__(self):
        """
        Implement pickling.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: f = G.aut().an_element()
            sage: f == loads(dumps(f))
            True
        """
        return (self.parent(), (self.matrix(),))

    def __call__(self,a):
        r"""
        Return the image of ``a`` under this automorphism.

        INPUT:

        - ``a`` -- something convertible into the domain

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4])
            sage: f = G.aut().an_element()
            sage: f
            [ g2^2, g1*g3^3, g1 ] -> [ g2, g3, g1*g3^2 ]
        """
        g = self.gap().ImageElm
        dom = self.parent()._domain
        a = dom(a)
        a = a.gap()
        return dom(g(a))

    def matrix(self):
        r"""
        Return the matrix defining ``self``.

        The `i`-th row is the exponent vector of
        the image of the `i`-th generator.

        OUTPUT:

        - a square matrix over the integers

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4])
            sage: f = G.aut().an_element()
            sage: f
            [ g2^2, g1*g3^3, g1 ] -> [ g2, g3, g1*g3^2 ]
            sage: f.matrix()
            [1 0 2]
            [0 2 0]
            [1 0 1]

        Compare with the exponents of the images::

            sage: f(G.gens()[0]).exponents()
            (1, 0, 2)
            sage: f(G.gens()[1]).exponents()
            (0, 2, 0)
            sage: f(G.gens()[2]).exponents()
            (1, 0, 1)
        """
        R = self.parent()._covering_matrix_ring
        coeffs = []
        for a in self.parent()._domain.gens():
            coeffs.append(self(a).exponents())
        m = R(coeffs)
        m.set_immutable()
        return m

class AbelianGroupAutomorphismGroup_generic(UniqueRepresentation,
                                            GroupMixinLibGAP,
                                            Group,
                                            ParentLibGAP):
    r"""
    Base class for groups of automorphisms of abelian groups.

    Do not use this directly

     INPUT:

    - ``domain`` -- :class:`~sage.groups.abelian_gps.abelian_group_gap.AbelianGroup_gap`
    - ``libgap_parent`` -- the libgap element that is the parent in
      GAP.
    - ``ambient`` -- A derived class of :class:`~sage.groups.libgap_wrapper.ParentLibGAP` or
      ``None`` (default). The ambient class if ``libgap_parent`` has
      been defined as a subgroup

    EXAMPLES::

        sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
        sage: from sage.groups.abelian_gps.abelian_aut import AbelianGroupAutomorphismGroup_generic
        sage: domain = AbelianGroupGap([2,3,4,5])
        sage: aut = domain.gap().AutomorphismGroupAbelianGroup()
        sage: AbelianGroupAutomorphismGroup_generic(domain, aut)
        <group with 6 generators>
    """
    Element = AbelianGroupAutomorphismGroupElement

    def __init__(self, domain, gap_group, ambient=None):
        """
        Constructor.

        Override this in derived classes.
        The input of the new method should be hashable in order for pickling
        and unique representation to work.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: G.aut()
            Full group of automorphisms of Abelian group with gap, generator orders (2, 3, 4, 5)
        """
        self._domain = domain
        n = len(self._domain.gens())
        self._covering_matrix_ring = MatrixSpace(ZZ, n)
        ParentLibGAP.__init__(self, gap_group, ambient=ambient)
        Group.__init__(self)

    def _element_constructor_(self, x, check=True):
        r"""
        Handle conversions and coercions.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: aut = G.aut()
            sage: f = aut.an_element()
            sage: f == aut(f.matrix())
            True
        """
        if x in self._covering_matrix_ring:
            dom = self._domain
            images = [dom(row).gap() for row in x.rows()]
            x = dom.gap().GroupHomomorphismByImages(dom.gap(),images)
        return self.element_class(self, x, check)

    def _coerce_map_from_(self, S):
        r"""
        Return whether ``S`` canonically coerces to ``self``.

        INPUT:

        - ``S`` -- anything.

        OUTPUT:

        Boolean.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: gen = G.gens()[:2]
            sage: S = G.subgroup(gen)
            sage: G._coerce_map_from_(S)
            True
            sage: S._coerce_map_from_(G)
            False
        """
        if isinstance(S, AbelianGroupAutomorphismGroup_generic):
            return S.is_subgroup_of(self)

    def _subgroup_constructor(self, libgap_subgroup):
        r"""
        Create a subgroup from the input.

        See :class:`~sage.groups.libgap_wrapper`

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: domain = AbelianGroupGap([2,3,4,5])
            sage: aut = domain.aut()
            sage: aut._subgroup_constructor(aut.gap())
            Subgroup of automorphisms of Abelian group with gap, generator orders (2, 3, 4, 5)
            generated by 6 automorphisms
        """
        ambient = self.ambient()
        generators = libgap_subgroup.GeneratorsOfGroup()
        generators = tuple(ambient(g) for g in generators)
        return AbelianGroupAutomorphismGroup_subgroup(ambient, generators)

    def domain(self):
        r"""
        Return the domain of this group of automorphisms.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: aut = G.aut()
            sage: aut.domain()
            Abelian group with gap, generator orders (2, 3, 4, 5)
        """
        return self._domain

    def is_subgroup_of(self, G):
        r"""
        Return if ``self`` is a subgroup of ``G`` considered in the same ambient group.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: aut = G.aut()
            sage: gen = aut.gens()
            sage: S1 = aut.subgroup(gen[:2])
            sage: S1.is_subgroup_of(aut)
            True
            sage: S2 = aut.subgroup(aut.gens()[1:])
            sage: S2.is_subgroup_of(S1)
            False
        """
        if not isinstance(G, AbelianGroupAutomorphismGroup_generic):
            raise ValueError("Input must be an instance of AbelianGroup_gap.")
        if not self.ambient() is G.ambient():
            return False
        return G.gap().IsSubsemigroup(self).sage()

class AbelianGroupAutomorphismGroup_ambient(AbelianGroupAutomorphismGroup_generic):
    r"""
    Full automorphism group of a finite abelian group.
    """
    Element = AbelianGroupAutomorphismGroupElement

    def __init__(self, AbelianGroupGap):
        """
        Group interface for LibGAP-based groups.

        INPUT:

        Same as :class:`~sage.groups.libgap_wrapper.ParentLibGAP`.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: aut = G.aut()
            sage: TestSuite(aut).run()
        """
        self._domain = AbelianGroupGap
        if not self._domain.is_finite():
            raise ValueError("Only finite abelian groups are supported.")
        G = libgap.AutomorphismGroup(self._domain.gap())
        AbelianGroupAutomorphismGroup_generic.__init__(self,
                                                       self._domain,
                                                       G,
                                                       ambient=None)
        Group.__init__(self)

    def __repr__(self):
        r"""
        String representation of ``self``.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: aut = G.automorphism_group()
        """
        s = "Full group of automorphisms of %s"%self.domain()
        return s

class AbelianGroupAutomorphismGroup_subgroup(AbelianGroupAutomorphismGroup_generic):
    r"""
    Groups of automorphisms of abelian groups.

    They are subgroups of the full automorphism group.
    Do not use this class directly instead use.
    meth:`subgroup`.

    INPUT:

    - ``ambient`` -- the ambient group. Usually this is the full group of
      automorphisms
    - ``generators`` -- a tuple of gap elements of the ambient group

    EXAMPLES::

        sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
        sage: from sage.groups.abelian_gps.abelian_aut import AbelianGroupAutomorphismGroup_subgroup
        sage: G = AbelianGroupGap([2,3,4,5])
        sage: aut = G.aut()
        sage: gen = aut.gens()
        sage: AbelianGroupAutomorphismGroup_subgroup(aut, gen)
        Subgroup of automorphisms of Abelian group with gap, generator orders (2, 3, 4, 5)
        generated by 6 automorphisms
    """
    Element = AbelianGroupAutomorphismGroupElement

    def __init__(self, ambient, generators):
        """
        Constructor.

        TESTS::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: aut = G.automorphism_group()
            sage: f = aut.an_element()
            sage: sub = aut.subgroup([f])
            sage: TestSuite(sub).run()
        """
        self._domain = ambient.domain()
        generators = tuple(g.gap() for g in generators)
        H = ambient.gap().Subgroup(generators)
        AbelianGroupAutomorphismGroup_generic.__init__(self,
                                                       self._domain,
                                                       H,
                                                       ambient=ambient)
        Group.__init__(self)
        self._covering_matrix_ring = ambient._covering_matrix_ring

    def __repr__(self):
        r"""
        The string representation of ``self``.

        EXAMPLES::

            sage: from sage.groups.abelian_gps.abelian_group_gap import AbelianGroupGap
            sage: G = AbelianGroupGap([2,3,4,5])
            sage: aut = G.automorphism_group()
            sage: f = aut.an_element()
            sage: sub = aut.subgroup([f])
        """
        s = "Subgroup of automorphisms of %s \n generated by %s automorphisms"%(
            self.domain(),len(self.gens()))
        return s