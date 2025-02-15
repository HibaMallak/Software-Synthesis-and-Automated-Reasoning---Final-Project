from final.syntax.tree import Tree
from final.syntax.tree.transform import TreeTransform


class TreeSubstitutionBase(TreeTransform):
    class Substitution:
        def __new__(cls, replace_with):
            return replace_with

    class Transformer:
        def __init__(self, replace_what, replace_with):
            self.replace_what = replace_what
            self.replace_with = replace_with

    def __init__(self, substitutions=None, *a, **kw):
        if substitutions is None:
            substitutions = {}
        super().__init__(
            [
                self.Transformer(k, self.substitution(v))
                for k, v in substitutions.items()
            ],
            *a,
            **kw
        )
        self.substitutions = substitutions

    def substitution(self, v):
        if isinstance(v, self.Substitution):
            return v
        else:
            return self.Substitution(v)


class TreeSubstitution(TreeSubstitutionBase):
    class Transformer(TreeSubstitutionBase.Transformer):
        def __call__(self, tree):
            w = self.replace_what
            if isinstance(w, type(tree)):
                compare_with = w
            else:
                compare_with = type(tree)(w)
            if tree.root == w and isinstance(self.replace_with, list):
                return type(tree)([], self.replace_with)
            if tree.root == w and not isinstance(self.replace_with, type(tree)):
                return TreeTransform.Scalar(self.replace_with)
            elif tree == compare_with:
                if isinstance(self.replace_with, list):
                    return type(tree)([], self.replace_with)
                elif isinstance(self.replace_with, type(tree)):
                    return self.replace_with
                else:
                    return type(tree)(self.replace_with)


class TreePatternSubstitution(TreeSubstitutionBase):
    """
    @see .tree.search.TreePattern
    """

    class Substitution:
        TreeSubstitution = TreeSubstitution

        def __init__(self, template):
            self.template = template

        def __call__(self, match_object):
            return self.TreeSubstitution(match_object.groups)(self.template)

        def __and__(self, precedes):
            return TreePatternSubstitution.SubstitutionChain([self]) & precedes

        def __repr__(self):
            return repr(self.template)

    class Transformer(TreeSubstitutionBase.Transformer):
        def __call__(self, tree):
            mo = self.replace_what.match(tree)
            if mo is not None:
                return self.replace_with(mo)

    class SubstitutionChain(list, Substitution):
        def __init__(self, *a):
            list.__init__(self, *a)

        def __call__(self, match_object):
            for substitution in self:
                retval = substitution(match_object)
                if retval is not None:
                    return retval

        def __and__(self, precedes):
            return type(self)([precedes] + self)

        def __repr__(self):
            return "; ".join(repr(x) for x in reversed(self))

    class AugmentSubstitution(Substitution):
        """
        Used for more advanced settings when you want to do some computable
        processing of the matched pattern.
        """

        def __init__(self, augment=None):
            super().__init__(None)
            self.augment = augment or {}

        def __call__(self, match_object):
            g = match_object.groups
            for k, v in self.augment.items():
                g[k] = v(g)

        def __repr__(self):
            return "(aug. %s)" % ",".join(repr(x) for x in self.augment.keys())

        def __rand__(self, template):
            if isinstance(template, Tree):
                return TreePatternSubstitution.Substitution(template) & self
            else:
                return NotImplemented


TreePatternSubstitution.Substitution.TreePatternSubstitution = TreePatternSubstitution
TreePatternSubstitution.AugmentSubstitution.TreePatternSubstitution = (
    TreePatternSubstitution
)


# Snippet
def main():
    from final.syntax.tree.build import TreeAssistant as TA
    from final.syntax.tree.search.pattern import TreeTopPattern

    tree = TA.build(("v", ["x", "y", "z"]))
    tsub = TreeSubstitution({TA.build("x"): [TA.build(x) for x in "abc"]})
    # print 'before:', tree
    # print 'after: ', tsub.inplace(tree)
    pat = TreeTopPattern(TA.build(("v", ["$..."])))
    psb = TA.build(("t", ["$...", "0"]))
    tpat = TreePatternSubstitution({pat: psb})
    # print 'pattern:', pat
    # print 'text:   ', tree
    # print tpat(tree)


if __name__ == "__main__":
    main()
