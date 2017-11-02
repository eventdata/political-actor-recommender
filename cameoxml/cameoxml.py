###########################################################################
# Copyright 2016 Raytheon BBN Technologies Corp. All Rights Reserved.     #
#                                                                         #
###########################################################################


"""
Python API for Accessing CameoXML Files.

    >>> import cameoxml
    >>> response = cameoxml.send_document('The American president Barack Obama met with a group of doctors.', hostname='127.0.0.1', port=9999)
    >>> cameo_doc = cameoxml.build_document_from_response(response)
    >>> print cameo_doc
    Document:
		sentences = Sentences:
			[
				<Sentence...>
			]
		events = Events:
			[
				<Event...>
				<Event...>
			]

or, to load a document from a file:

    >>> cameo_doc = cameoxml.Document(filename)

For a list of attributes that any theory object, use the
'help' method on the theory object (or its class).  E.g.:

    >>> cameo_doc.sentences[0].help()
"""

import os, re, select, socket, sys, textwrap, weakref
from optparse import OptionParser
from xml.etree import ElementTree as ET

def escape_cdata_carriage_return(text, encoding):
    """
    Source copied from ElementTree.py and modified to add
    '\r' -> '&#xD;' replacement. Monkey patch!
    """
    # escape character data
    try:
        # it's worth avoiding do-nothing calls for strings that are
        # shorter than 500 character, or so.  assume that's, by far,
        # the most common case in most applications.
        if "&" in text:
            text = text.replace("&", "&amp;")
        if "<" in text:
            text = text.replace("<", "&lt;")
        if ">" in text:
            text = text.replace(">", "&gt;")
        if "\r" in text:
            text = text.replace("\r", "&#xD;")
        return text.encode(encoding, "xmlcharrefreplace")
    except (TypeError, AttributeError):
        ET._raise_serialization_error(text)

ET._escape_cdata = escape_cdata_carriage_return

"""If true, then Theory objects will keep a pointer to the
   ElementTree.Element that they were constructed from.  This
   makes it possible for the save() method to preserve any extra
   attributes or elements that were present in the original
   document."""
KEEP_ORIGINAL_ETREE = False

######################################################################
#{ Theory Attribute Specifications
######################################################################

class _AutoPopulatedXMLAttributeSpec(object):
    """
    This is the abstract base class for \"Auto-populated XML attribute
    specifications\" (or AttributeSpec's for short).  Each
    AttributeSpec is used to define a single attribute for a
    theory class.  Some examples of AttributeSpecs are::
        
        sentences    = _ChildTheoryElement('Sentences')

    Each AttributeSpec defines a `set_value()` method, which is used
    to read the attribute's value from the XML input for a given
    theory object.  The default implementation of `set_value()` calls
    the abstract method `get_value()`, which should read the
    appropriate value from a given XML node, and stores it in the
    theory object (using `setattr`).

    The name of the instance variable that is used to store an
    attribute's value is always identical to the name of the class
    variable that holds the AttributeSpec.  For example, the Document
    class contains an AttributeSpec named 'docid'; and each instance
    of the Document class will have an instance variable with the same
    name ('docid') that is initialized by that AttributeSpec.  Note
    that this instance variable (containing the attribute value)
    shadows the class variable containing the AttributeSpec.
    """

    # We assign a unique attribute number to each AttributeSpec that
    # gets created.  This allows us to display attributes in the
    # correct order when pretty-printing.  (In particular, attributes
    # are displayed in the order in which they were defined.)
    attribute_counter = 0
    def __init__(self):
        self._attribute_number = self.attribute_counter
        _AutoPopulatedXMLAttributeSpec.attribute_counter += 1

    def set_value(self, etree, theory):
        """
        Set the value of this attribute.

        @param name: The name that should be used to store the attribute.
        @param etree: The (input) XML tree corresponding to `theory`.
        @param theory: The theory object, to which the attribute
            should be added.
        """
        setattr(theory, self.__name__, self.get_value(etree, theory))

    def get_value(self, etree, theory):
        """
        Extract and return the value of this attribute from an input
        XML tree.

        @param name: The name that should be used to store the attribute.
        @param etree: The (input) XML tree corresponding to `theory`.
        @param theory: The theory object, to which the attribute
            should be added.
        """
        raise AssertionError('get_value() is an abstract method.')

    def serialize(self, etree, theory, **options):
        raise AssertionError('serialize() is an abstract method.')

    def default_value(self):
        return None

    def help(self):
        """
        Return a single-line string describing this attribute
        """
        raise AssertionError('help() is an abstract method.')

class _SimpleAttribute(_AutoPopulatedXMLAttributeSpec):
    """
    A basic theory attribute, whose value is copied directly
    from a corresonding XML attribute.  The value should have a simple
    type (such as string, boolean, or integer).
    """
    def __init__(self, value_type=unicode, default=None, attr_name=None,
                 is_required=False):
        """
        @param value_type: The type of value expected for this attribute.
            This should be a Python type (such as int or bool), and is
            used directly to cast the string value to an appropriate value.
        @param default: The default value for this attribute.  I.e., if
            no value is provided, then the attribute will take this value.
            The default value is *not* required to be of the type specified
            by value_type -- in particular, the default may be None.
        @param attr_name: The name of the XML attribute used to store this
            value.  If not specified, then the name will default to the
            name of the theory attribute.
        @param is_required: If true, then raise an exception if this
            attribute is not defined on the XML input element.
        """
        _AutoPopulatedXMLAttributeSpec.__init__(self)
        self._value_type = value_type
        self._default = default
        self._attr_name = attr_name
        self._is_required = is_required

    def get_value(self, etree, theory):
        name = self._attr_name or self.__name__
        if name in etree.attrib:
            return self._parse_value(name, etree.attrib[name])
        elif self._is_required:
            raise ValueError('Attribute %s is required for %s' %
                             (name, etree))
        else:
            return self._default

    def _parse_value(self, name, value):
        if self._value_type == bool:
            if value.lower() == 'true': return True
            if value.lower() == 'false': return False
            raise ValueError('Attribute %s must have a boolean value '
                             '(either TRUE or FALSE)' % name)
        else:
            return self._value_type(value)

    def _encode_value(self, value):
        if value is True:
            return 'TRUE'
        elif value is False:
            return 'FALSE'
        elif isinstance(value, str):
            return value.decode('utf-8')
        elif isinstance(value, EnumeratedType._BaseClass):
            return value.value
        elif not isinstance(value, unicode):
            return unicode(value)
        else:
            return value

    def serialize(self, etree, theory, **options):
        value = getattr(theory, self.__name__, None)
        explicit_defaults = options.get('explicit_defaults', False)
        if value is not None:
            if ((not explicit_defaults) and
                (self._default is not None) and
                (value == self._default)):
                return
            attr_name = self._attr_name or self.__name__
            value = self._encode_value(value)
            etree.attrib[attr_name] = value

    _HELP_TEMPLATE = 'a %s value extracted from the XML attribute %r'
    def help(self):
        name = self._attr_name or self.__name__
        s = self._HELP_TEMPLATE % (
            self._value_type.__name__, name)
        if self._is_required:
            s += ' (required)'
        else:
            s += ' (default=%r)' % self._default
        return s

class _ReferenceAttribute(_SimpleAttribute):
    """
    An attribute that is used to point to another theory object,
    using its identifier.  When this attribute is initialized, the
    target id is copied from the XML attribute with a specified name
    (`attr_name`), and stored as a private variable.  This id is *not*
    looked up during initialization, since its target may not have
    been created yet.

    Instead, this attribute uses a Python feature called
    \"descriptors\" to resolve the target id to a value when the
    attribute is accessed.

    In particular, each _ReferencedAttribute is a (non-data)
    descriptor on the theory class, which means that its
    `__get__()` method is called whenever the corresponding
    theory attribute is read.  The `__get__()` method looks up the
    target id in the identifier map that is owned by the theory's
    document.  If the identifier is found, then the corresponding
    theory object is returned; otherwise, a special `DanglingPointer`
    object is returned.
    """
    def __init__(self, attr_name, is_required=False, cls=None):
        """
        @param attr_name: The name of the XML idref attribute used to
            hold the pointer to a theory object.  Typically, these
            attribute names will end in '_id'.
        @param is_required: If true, then raise an exception if this
            attribute is not defined on the XML input element.  If
            is_required is false and the attribute is not defined on
            the XML input element, then the theory attribute's
            value will be None.
        @param cls: The theory class (or name of the class)
            that the target value should belong to.
        """
        self._attr_name = attr_name
        self._private_attr_name = '_' + attr_name
        self._cls = cls
        _SimpleAttribute.__init__(self, is_required=is_required,
                                  attr_name=attr_name)

    def set_value(self, etree, theory):
        # This stores the id, but does *not* look it up -- the target
        # for the pointer might not have been deserialized from xml yet.
        setattr(theory, self._private_attr_name,
                self.get_value(etree, theory))

    def serialize(self, etree, theory, **options):
        child = getattr(theory, self.__name__, None)
        if child is not None:
            etree.attrib[self._attr_name] = self._get_child_id(child)

    def _get_child_id(self, child):
        child_id = getattr(child, 'id', None)
        if child_id is None:
            raise ValueError('Serialization Error: attempt to serialize '
                             'a pointer to an object that has no id (%r)'
                             % child)
        return child_id

    def __get__(self, instance, owner=None):
        # We look up the id only when the attribute is accessed.
        if instance is None: return self
        theory_id = getattr(instance, self._private_attr_name)
        if theory_id is None: return None
        document = instance.document
        if document is None:
            return DanglingPointer(theory_id)
        target = document.lookup_id(theory_id)
        if target is None:
            return DanglingPointer(theory_id)
        if self._cls is not None:
            if isinstance(self._cls, basestring):
                self._cls = Theory._theory_classes[self._cls]
            if not isinstance(target, self._cls):
                raise ValueError('Expected %s to point to a %s' % (
                    self._attr_name, self._cls.__name__))
        return target

    def _cls_name(self):
        if self._cls is None:
            return 'theory object'
        elif isinstance(self._cls, basestring):
            return self._cls
        else:
            return self._cls.__name__

    def help(self):
        name = self._attr_name or self.__name__
        s = 'a pointer to a %s extracted from the XML attribute %r' % (
            self._cls_name(), name)
        if self._is_required: s += ' (required)'
        return s

class DanglingPointer(object):
    """
    A class used by `_ReferenceAttribute` to indicate that the target
    id has not yet been read.  In particular, a DanglingPointer will
    be returned by `ReferenceAttribute.__get__()` if a target pointer
    id is not found in the identifier map.
    """
    def __init__(self, id1):
        self.id = id1
    def __repr__(self):
        return "<Dangling Pointer: id=%r>" % self.id
    def _get_summary(self):
        return "<Dangling Pointer: id=%r>" % self.id

class _OffsetAttribute(_AutoPopulatedXMLAttributeSpec):
    """
    An attribute used to store a start or end offset.  These
    attributes may be stored in the XML in two different ways: either
    using separate XML attributes for the begin and end offsets; or
    using a single XML attribute for both.  This AttributeSpec
    subclass is responsible for reading both formats.
    """
    def __init__(self, offset_side, offset_name, value_type=int):
        _AutoPopulatedXMLAttributeSpec.__init__(self)
        assert offset_side in ('start', 'end')
        self.is_start = (offset_side == 'start')
        self.offset_name = offset_name
        self.offset_attr = '%s_%s' % (offset_side, offset_name)
        self.condensed_offsets_attr = '%s_offsets' % offset_name
        self._value_type = value_type

    def get_value(self, etree, theory):
        if self.offset_attr in etree.attrib:
            return self._value_type(etree.attrib[self.offset_attr])
        elif self.condensed_offsets_attr in etree.attrib:
            s, e = etree.attrib[self.condensed_offsets_attr].split(':')
            if self.is_start: return self._value_type(s)
            else: return self._value_type(e)
        else:
            return None

    def serialize(self, etree, theory, **options):
        value = getattr(theory, self.__name__, None)
        if value is not None:
            if options.get('condensed_offsets', True):
                etree.attrib[self.condensed_offsets_attr] = '%s:%s' % (
                    getattr(theory, 'start_%s' % self.offset_name),
                    getattr(theory, 'end_%s' % self.offset_name))
            else:
                etree.attrib[self.offset_attr] = '%s' % value

    def help(self):
        return 'an offset extracted from XML attribute %r or %r' % (
            (self.offset_attr, self.condensed_offsets_attr))

class _ChildTheoryElement(_AutoPopulatedXMLAttributeSpec):
    """
    An attribute used to hold a child theory that is described in
    a child XML element.
    """
    def __init__(self, cls_name, is_required=False):
        """
        @param cls_name: The name of the theory class for the
            child value.
        """
        _AutoPopulatedXMLAttributeSpec.__init__(self)
        self._is_required = is_required
        self._cls_name = cls_name

    def _get_child_elt(self, name, etree):
        if isinstance(name, tuple):
            elts = [elt for elt in etree if elt.tag in name]
            name = ' or '.join(name) # for error messages.
        else:
            elts = [elt for elt in etree if elt.tag == name]
        if len(elts) == 1:
            return elts[0]
        elif len(elts) > 1:
            raise ValueError('Expected at most one %s' % name)
        elif self._is_required:
            raise ValueError('Expected exactly one %s' % name)
        else:
            return None

    def serialize(self, etree, theory, **options):
        child = getattr(theory, self.__name__, None)
        if child is not None:
            if (hasattr(child, '_etree') and child._etree in etree):
                child_etree = child.toxml(child._etree, **options)
            else:
                child_etree = child.toxml(**options)
                etree.append(child_etree)
            if isinstance(self._cls_name, tuple):
                assert child_etree.tag in self._cls_name
            else:
                assert child_etree.tag == self._cls_name

    def get_value(self, etree, theory):
        name = self._cls_name or self.__name__
        child_elt = self._get_child_elt(name, etree)
        if child_elt is None:
            return None
        cls = Theory._theory_classes.get(child_elt.tag)
        if cls is None:
            raise AssertionError('Theory class %s not defined!' % name)
        return cls(child_elt, theory)

    def help(self):
        s = 'a child %s theory' % self._cls_name
        if self._is_required: s += ' (required)'
        else: s += ' (optional)'
        return s

class _ChildTextElement(_ChildTheoryElement):
    """
    An attribute whose value should be extracted from the string text
    of a child XML element.  (c.f. _TextOfElement)
    """
    def get_value(self, etree, theory):
        child_elt = self._get_child_elt(self._cls_name, etree)
        if KEEP_ORIGINAL_ETREE:
            self._child_elt = child_elt
        if child_elt is None:
            return None
        else:
            return child_elt.text

    def serialize(self, etree, theory, **options):
        text = getattr(theory, self.__name__, None)
        if text is not None:
            if hasattr(self, '_child_elt') and self._child_elt in etree:
                child_etree = self._child_elt
            else:
                del etree[:]
                child_etree = ET.Element(self._cls_name or self.__name__)
                etree.append(child_etree)
            child_etree.text = text
            child_etree.tail = '\n'+options.get('indent', '')

    def help(self):
        return 'a text string extracted from the XML element %r' % (
            self._cls_name)

class _TextOfElement(_AutoPopulatedXMLAttributeSpec):
    """
    An attribute whose value should be extracted from the string text
    of *this* XML element.  (c.f. _ChildTextElement)
    """
    def __init__(self, is_required=False, strip=False):
        _AutoPopulatedXMLAttributeSpec.__init__(self)
        self._strip = strip
        self._is_required = is_required
    def get_value(self, etree, theory):
        text = etree.text or ''
        if self._strip: text = text.strip()
        if self._is_required and not text:
            raise ValueError('Text content is required for %s' %
                             self.__name__)
        return text

    def serialize(self, etree, theory, **options):
        text = getattr(theory, self.__name__, None)
        if text is not None:
            #assert etree.text is None # only one text string!
            etree.text = text

    def help(self):
        return ("a text string extracted from this "
                "theory's XML element text")

class _ChildTheoryElementList(_AutoPopulatedXMLAttributeSpec):
    """
    An attribute whose value is a list of child theories.  Each child
    theory is deserialized from a single child XML element.
    """
    def __init__(self, cls_name, index_attrib=None):
        _AutoPopulatedXMLAttributeSpec.__init__(self)
        self._cls_name = cls_name
        self._index_attrib = index_attrib

    def get_value(self, etree, theory):
        name = self._cls_name or self.__name__
        elts = [elt for elt in etree if elt.tag == name]
        cls = Theory._theory_classes.get(name)
        if cls is None:
            raise AssertionError('Theory class %s not defined!' % name)
        result = [cls(elt, theory) for elt in elts]
        if self._index_attrib:
            for i, child in enumerate(result):
                child.__dict__[self._index_attrib] = i
        return result

    def serialize(self, etree, theory, **options):
        children = getattr(theory, self.__name__, ())
        if KEEP_ORIGINAL_ETREE:
            child_etrees = set(etree)
        else:
            child_etrees = set()
        for child in children:
            if (hasattr(child, '_etree') and child._etree in child_etrees):
                child_etree = child.toxml(child._etree, **options)
            else:
                child_etree = child.toxml(**options)
                etree.append(child_etree)
            assert child_etree.tag == self._cls_name

    def default_value(self):
        return []

    def help(self):
        s = 'a list of child %s theory objects' % self._cls_name
        return s

######################################################################
#{ Enumerated Type metaclass
######################################################################

class EnumeratedType(type):
    """
    >>> colors = EnumeratedType('colors', 'red green blue')
    >>> assert colors.red != colors.green
    >>> assert colors.red == colors.red
    """
    class _BaseClass(object):
        def __init__(self, value):
            self.__value = value
            self.__hash = hash(value)
        def __repr__(self):
            return '%s.%s' % (self.__class__.__name__, self.__value)
        def __hash__(self):
            return self.__hash
        def __cmp__(self, other):
            if self.__class__ != other.__class__:
                raise ValueError(
                    "Attempt to compare %r value with %r value -- only "
                    "values from the same enumeration are comparable!" %
                    (self.__class__.__name__, other.__class__.__name__))
            return cmp(self.__value, other.__value)
        @property
        def value(self):
            return self.__value
    def __new__(cls, name, values):
        return type.__new__(cls, name, (cls._BaseClass,), {})
    def __init__(cls, name, values):
        if isinstance(values, basestring):
            values = values.split()
        cls.values = [cls(value) for value in values]
        for enum_name, enum_value in zip(values, cls.values):
            setattr(cls, enum_name, enum_value)
    def __iter__(self):
        return iter(self.values)
    def __len__(self):
        return len(self.values)
    def __getitem__(self, i):
        return self.values[i]
    def __repr__(self):
        return '<%s enumeration: %r>' % (self.__name__, tuple(self.values),)

######################################################################
#{ Theory Objects Base Classes
######################################################################

class Theory(object):
    """
    The base class for theory types.
    """
    _theory_classes = {}
    class __metaclass__(type):
        def __init__(cls, name, bases, dct):
            type.__init__(cls, name, bases, dct)
            # Register the class in a registry.
            cls.__theory_name__ = name
            if hasattr(cls, '__overrides__'):
                cls.__theory_name__ = cls.__overrides__
            #elif name in cls._theory_classes:
            #    print "Warning: overriding %s!" % name
            cls._theory_classes[cls.__theory_name__] = cls

            # Add an _auto_attribs attribute
            cls._auto_attribs = [
                (k,v) for (k,v) in dct.items()
                if isinstance(v, _AutoPopulatedXMLAttributeSpec)]
            for attr_name, attr_spec in cls._auto_attribs:
                attr_spec.__name__ = attr_name
            for base in bases:
                cls._auto_attribs.extend(getattr(base, '_auto_attribs', []))
            def sort_key(attrib):
                return (attrib[1]._attribute_number, attrib[0].lower())
            cls._auto_attribs.sort(key=sort_key)

    _OWNER_IS_REQUIRED = True

    def __init__(self, etree=None, owner=None, **attribs):
        # Set our owner pointer.
        if owner is not None:
            self._owner = weakref.ref(owner)
        elif self._OWNER_IS_REQUIRED:
            raise ValueError('%s constructor requires an owner' %
                             self.__class__.__name__)
        else:
            self._owner = None
        # Intialize, either from etree or from attributes.
        if etree is not None:
            if attribs:
                raise ValueError('Specify etree or attribs, not both!')
            self._init_from_etree(etree, owner)
        else:
            for attr_name, attr_spec in self._auto_attribs:
                value = attribs.pop(attr_name, None)
                if value is not None:
                    setattr(self, attr_name, value)
                else:
                    setattr(self, attr_name, attr_spec.default_value())

    def _init_from_etree(self, etree, owner):
        assert etree is not None
        if etree.tag != self.__class__.__theory_name__:
            raise ValueError('Expected a %s, got a %s!' %
                             (self.__class__.__theory_name__, etree.tag))
        if KEEP_ORIGINAL_ETREE:
            self._etree = etree
        # Fill in any attribute values
        for _, attr in self._auto_attribs:
            attr.set_value(etree, self)

    def toxml(self, etree=None, **options):
        """
        If `etree` is specified, then this theory object will be
        serialized into that element tree Element; otherwise, a new
        Element will be created.
        """
        #print 'serializing %s' % self.__class__.__theory_name__
        indent = options.get('indent')
        if indent is not None: options['indent'] += '  '

        if etree is None:
            etree = ET.Element(self.__class__.__theory_name__)
        else:
            assert etree.tag == self.__class__.__theory_name__, (
                etree.tag, self.__class__.__theory_name__)

        for _, attr in self._auto_attribs:
            attr.serialize(etree, self, **options)

        # Indentation...
        if len(etree) > 0 and indent is not None:
            etree.text = '\n' + indent+'  '
            for child in etree[:-1]:
                child.tail = '\n' + indent+'  '
            etree[-1].tail = '\n' + indent
        if indent is not None: options['indent'] = indent
        etree.tail = '\n'
        return etree

    def pprint(self, depth=-1, hide=(), follow_pointers=False,
               indent='  ', memo=None):
        """
        Return a pretty-printed string representation of this
        theory object.  The first line identifies this theory object,
        and the subsequent lines describe its contents (including
        nested or referenced theory objects).

        @param depth: The maximum depth to which nested theory objects
            should be displayed.
        @param hide: A set of names of attributes that should not
            be displayed.  (By default, the XML id and the EDT and
            byte offsets are not displayed by __str__).
        @param follow_pointers: If true, then attributes that contain
            pointers have their contents displayed just like nested
            elements.  If false, then the pointer targets are not
            expanded.
        """
        if memo is None: memo = set()
        if id(self) in memo:
            return '<%s...>' % self.__class__.__theory_name__
        memo.add(id(self))
        s = self._pprint_firstline(indent)
        for attr_name, attr_spec in self.__class__._auto_attribs:
            if attr_name in hide: continue
            val = getattr(self, attr_name)
            if attr_name == '_children': attr_name = ''
            elif attr_name.startswith('_'): continue
            attr_depth = depth
            if (not follow_pointers and val is not None and
                isinstance(attr_spec, _ReferenceAttribute)
                and not isinstance(val, DanglingPointer)):
                s += '\n%s%s = <%s...>' % (
                    indent, attr_name, getattr(val.__class__, '__theory_name__',
                                               val.__class__.__name__))
            else:
                s += '\n'+self._pprint_value(attr_name, val, attr_depth, hide,
                                             follow_pointers, indent, memo)
        return s

    def _get_summary(self):
        return None

    def _pprint_firstline(self, indent):
        s = self.__class__.__theory_name__ + ':'
        text = self._get_summary()
        if text:
            maxlen = max(9, 65-len(indent)-
                         len(self.__class__.__theory_name__)*2)
            s += ' %s' % _truncate(text, maxlen)
        return s

    def _pprint_value(self, attr, val, depth, hide,
                      follow_pointers, indent, memo):
        s = indent
        if attr: s += attr + ' = '
        if isinstance(val, Theory):
            if depth is not None and depth == 0:
                return s+'<%s...>' % getattr(val.__class__, '__theory_name__',
                                             val.__class__.__name__)
            return s+val.pprint(depth-1, hide, follow_pointers,
                                indent+'  ', memo)
        elif isinstance(val, list):
            if len(val) == 0: return s+'[]'
            if depth is not None and depth == 0: return s+'[...]'
            items = [self._pprint_value('', item, depth-1, hide,
                                        follow_pointers, indent+'  ', memo)
                     for item in val]
            if depth == 1 and len(items) > 12:
                items = items[:10] + ['%s  ...and %d more...' %
                                      (indent, len(items)-10)]
            s += '[\n%s\n%s]' % ('\n'.join(items), indent)
            return s
        elif isinstance(val, basestring):
            text=repr(val)
            maxlen = max(9, 75-len(s))
            if len(text) > maxlen:
                text = text[:maxlen-9]+'...'+text[-6:]
            return s+text
        else:
            return s+repr(val)

    _default_hidden_attrs = set(['id', 'start_byte', 'end_byte',
                                 'start_edt', 'end_edt'])
    def __repr__(self):
        text = self._get_summary()
        if text:
            return '<%s %s>' % (self.__class__.__theory_name__, text)
        else:
            return '<%s>' % self.__class__.__theory_name__
    def __str__(self):
        return self.pprint(depth=2, hide=self._default_hidden_attrs,
                           follow_pointers=False)

    @property
    def owner(self):
        """The theory object that owns this Theory"""
        if self._owner is None: return None
        else: return self._owner()

    def owner_with_type(self, theory_class):
        """
        Find and return the closest owning theory with the given
        class.  If none is found, return None.  E.g., use
        tok.owner(Sentence) to find the sentence containing a token.
        """
        if isinstance(theory_class, basestring):
            theory_class = Theory._theory_classes[theory_class]
        theory = self
        while theory is not None and not isinstance(theory, theory_class):
            if theory._owner is None: return None
            theory = theory._owner()
        return theory

    @property
    def document(self):
        """The document that contains this Theory"""
        return self.owner_with_type(Document)

    def resolve_pointers(self, fail_on_dangling_pointer=True):
        """
        Replace reference attributes with their actual values for this
        theory and any theory owned by this theory (directly or
        indirectly).  Prior to calling this, every time you access a
        reference attribute, its value will be looked up in the
        document's identifier map.

        @param fail_on_dangling_pointer: If true, then raise an exception
        if we find a dangling pointer.
        """
        for attr_name, attr_spec in self._auto_attribs:
            attr_val = getattr(self, attr_name)
            # Replace any reference attribute w/ its actual value (unless
            # it's a dangling pointer)
            if isinstance(attr_spec, _ReferenceAttribute):
                if attr_name not in self.__dict__:
                    if not isinstance(attr_val, DanglingPointer):
                        setattr(self, attr_name, attr_val)
                    elif fail_on_dangling_pointer:
                        raise ValueError('Dangling pointer: %r' % attr_val)

            # Recurse to any owned objects.
            elif isinstance(attr_val, Theory):
                attr_val.resolve_pointers(fail_on_dangling_pointer)

    @classmethod
    def _help_header(cls):
        return 'The %r class defines the following attributes:' % (
            cls.__theory_name__)

    @classmethod
    def help(cls):
        props = [(k,v) for base in cls.mro()
                 for (k,v) in base.__dict__.items()
                 if isinstance(v, property)]

        s = cls._help_header()+'\n'
        w = max([8]+[len(n) for (n,_) in cls._auto_attribs]+
                [len(n) for (n,_) in props])+2
        for attr_name, attr_spec in cls._auto_attribs:
            if attr_name == '_children': continue
            help_line = textwrap.fill(attr_spec.help(),
                                      initial_indent=' '*(w+3),
                                      subsequent_indent=' '*(w+3)).strip()
            s += '  %s %s\n' % (attr_name.ljust(w, '.'), help_line)
        if props:
            s += ('The following derived properties are also '
                  'available as attributes:\n')
            for (k,v) in props:
                help_text = v.__doc__ or '(undocumented)'
                help_text = help_text.replace(
                    'this Theory', 'this '+cls.__theory_name__)
                help_text = ' '.join(help_text.split())
                help_line = textwrap.fill(
                    help_text,
                    initial_indent=' '*(w+3),
                    subsequent_indent=' '*(w+3)).strip()
                s += '  %s %s\n' % (k.ljust(w, '.'), help_line)

        print s.rstrip()

def _truncate(text, maxlen):
    if text is None:
        return None
    elif len(text) <= maxlen:
        return text
    else:
        return text[:maxlen-9]+'...'+text[-6:]

class DocumentTheory(Theory):
    def __init__(self, etree=None, owner=None, **attribs):
        self._idmap = weakref.WeakValueDictionary()
        Theory.__init__(self, etree, owner, **attribs)

    _OWNER_IS_REQUIRED = False
    def _init_from_etree(self, etree, owner):
        # If the argument isn't an etree, then create one.
        if hasattr(etree, 'makeelement'):
            pass # ok.
        elif hasattr(etree, 'getroot'):
            etree = etree.getroot() # ElementTree object
        elif isinstance(etree, basestring):
            if re.match('^\s*<', etree):
                etree = ET.fromstring(etree) # xml string
            elif '\n' not in etree:
                etree = ET.parse(etree).getroot() # filename
            else:
                raise ValueError('Expected a filename, xml string, stream, '
                                 'or ElementTree.  Got a %s' %
                                 etree.__class__.__name__)
        elif hasattr(etree, 'read'):
            etree = ET.fromstring(etree.read()) # file object
        else:
            raise ValueError('Expected a filename, xml string, stream, '
                             'or ElementTree.  Got a %s' %
                             etree.__class__.__name__)
        
        # If we got a CAMEO_XML element, then take its document.
        if (etree.tag == 'CAMEO_XML' and len(etree) == 1 and etree[0].tag == 'Document'):
            etree = etree[0]
        Theory._init_from_etree(self, etree, owner)
        # Resolve pointers.
        self.resolve_pointers()

    def save(self, file_or_filename):
        cameoxml_etree = ET.Element('Document')
        cameoxml_etree.text = '\n  '
        etree=getattr(self, '_etree', None)
        cameoxml_etree.append(self.toxml(etree, indent='  '))
        ET.ElementTree(cameoxml_etree).write(file_or_filename)

    def register_id(self, theory):
        if theory.id is not None:
            if theory.id in self._idmap:
                raise ValueError('Duplicate id %s' % theory.id)
            self._idmap[theory.id] = theory

    def lookup_id(self, theory_id):
        return self._idmap.get(theory_id)

    _default_hidden_attrs = set(['lexicon'])

class SequenceTheory(Theory):
    _children = "This class attr must be defined by subclasses."
    def __len__(self):
        return len(self._children)
    def __iter__(self):
        return self._children.__iter__()
    def __contains__(self, item):
        return self._children.__contains__(item)
    def __getitem__(self, n):
        return self._children.__getitem__(n)
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__theory_name__, self._children)
    def resolve_pointers(self, fail_on_dangling_pointer=True):
        Theory.resolve_pointers(self, fail_on_dangling_pointer)
        for child in self._children:
            child.resolve_pointers(fail_on_dangling_pointer)
    @classmethod
    def _help_header(cls):
        child_class_name = cls._children._cls_name
        return textwrap.fill(
            'The %r class acts as a sequence of %r elements.  '
            'Additionally, it defines the following attributes:'
            % (cls.__theory_name__, child_class_name))

######################################################################
#{ Theory Classes
######################################################################

class Document(DocumentTheory):
    sentences           = _ChildTheoryElement('Sentences')
    events              = _ChildTheoryElement('Events')

class Sentences(SequenceTheory):
    _children           = _ChildTheoryElementList('Sentence', index_attrib='sent_no')

class Sentence(Theory):
    id                  = _SimpleAttribute(is_required=True)
    char_offsets        = _SimpleAttribute(is_required=True)
    contents            = _TextOfElement('Contents')

class Events(SequenceTheory):
    _children           = _ChildTheoryElementList('Event')

class Event(Theory):
    id                  = _SimpleAttribute(is_required=True)
    participants        = _ChildTheoryElementList('Participant')
    type                = _SimpleAttribute(is_required=True)
    tense               = _SimpleAttribute(is_required=True)
    sentence_id         = _SimpleAttribute(is_required=True)

class Participant(Theory):
    role                = _SimpleAttribute(default='')
    actor_id            = _SimpleAttribute(default='')
    actor_name            = _SimpleAttribute(default='')
    agent_id            = _SimpleAttribute(default='')
    agent_name            = _SimpleAttribute(default='')

######################################################################
# ACCENT HTTP Server
######################################################################

HOSTNAME = 'localhost'
PORT = 9999

PROCESS_DOCUMENT_TEMPLATE = r'''
<SerifXMLRequest>
  <ProcessDocument end_stage="%(end_stage)s" output_format="CAMEOXML" input_type="%(input_type)s" %(date_string)s>
    %(document)s
  </ProcessDocument>
</SerifXMLRequest>
'''

DOCUMENT_TEMPLATE = r'''
<Document language="%(language)s" docid="%(docid)s">
  <OriginalText><Contents>%(content)s</Contents></OriginalText>
</Document>
'''

def send_pd_request(document, hostname=HOSTNAME, port=PORT,
                    end_stage='output', input_type='auto', verbose=False, document_date=None, 
                    timeout=0, num_tries=1):
    """
    Send a XML request to process the given document to the
    specified server.  If successful, then return a `Document` object
    containing the processed document.  If unsuccessful, then raise an
    exception with the response message from the server.

    @param document: A string containing an XML <Document> element.
    @param hostname: The hostname of the HTTP server.
    @param port: The port on which the HTTP server is listening.
    @param end_stage: The end stage for processing.
    """
    
    try:
        document.decode('utf-8')
    except UnicodeError:
        raise ValueError("Document is not UTF-8")
        
    date_string = ""
    if document_date:
        date_string = "document_date=\"" + document_date + "\""

    request = PROCESS_DOCUMENT_TEMPLATE % dict(
        document=document, end_stage=end_stage, input_type=input_type, date_string=date_string)
    
    response = send_request(
        'POST SerifXMLRequest', request,
        verbose=verbose, hostname=hostname, port=port, timeout=timeout, num_tries=num_tries)

    return response

def escape_xml(s):
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('\r', '&#xD;')
    return s


def send_document(content, docid='anonymous', language='English',
                  hostname=HOSTNAME, port=PORT,
                  end_stage='output', input_type='auto', document_date=None, 
                  verbose=False, timeout=0, num_tries=1):
    """
    Create a <Document> object from the given text content and docid,
    and use `send_pd_request()` to send it to am ACCENT HTTP
    server.  If successful, then return a `Document` object containing
    the processed document.  If unsuccessful, then raise an exception
    with the response message from the server.

    @param content: The text content that should be processed by ACCENT.
    @param docid: The document identifier for the created <Document>.
    @param language: The language used by the document.
    @param hostname: The hostname of the ACCENT HTTP server.
    @param port: The port on which the ACCENT HTTP server is listening.
    @param end_stage: The end stage for processing.
    """
    xml_request = DOCUMENT_TEMPLATE % dict(
        docid=docid, content=escape_xml(content), language=language)
    response = send_pd_request(xml_request, end_stage=end_stage, input_type=input_type,
                               verbose=verbose, hostname=hostname, port=port, timeout=timeout, 
                               num_tries=num_tries, document_date=document_date)
    return response

def build_document_from_response(response):
    if re.match('HTTP/.* 200 OK', response):
        body = response.split('\r\n\r\n', 1)[1]
        return Document(ET.fromstring(body))
    else:
        raise ValueError(response)

def send_request(header, msg, hostname=HOSTNAME, port=PORT,
                 verbose=False, timeout=0, num_tries=1):
    """
    Send an HTTP request message to the ACCENT server, and return
    the response message (as a string).
    """
    # Construct the HTTP request message.
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')  # If we have a non-ascii msg, make sure we encode it as utf-8
    request = (header + " HTTP/1.0\r\n" +
               "content-length: %d\r\n\r\n" % len(msg) + msg)
    if verbose:
        DIV = '-' * 75
        print '%s\n%s%s' % (DIV, request.replace('\r\n', '\n'), DIV)
        
    for attempt in range(num_tries):
        if attempt > 0:
            print "send_request() on attempt %d of %d" % (attempt + 1, num_tries)

        # Send the message.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.connect((hostname, int(port)))
        s.sendall(request)
        s.setblocking(0)

        # Read and return the response.
        result = ''
        inputs = [s]
        problem_encountered = False
        while inputs and not problem_encountered:
            if timeout > 0:
                rlist, _, xlist = select.select(inputs, [], inputs, timeout)
            else:
                rlist, _, xlist = select.select(inputs, [], inputs)
            for s in rlist:
                data = s.recv(4096)
                #print "send_request() received data of length %d" % len(data)
                if data:
                    result += data
                else:
                    inputs.remove(s)
                    s.close()
            for s in xlist:
                print "send_request() handling exceptional condition for %s" % s.getpeername()
                problem_encountered = True
                inputs.remove(s)
                s.close()
            if rlist == [] and xlist == []:
                print "send_request() timed out while waiting for input from the socket!"
                problem_encountered = True
                inputs.remove(s)
                s.close()
        if problem_encountered:
            if result.endswith('</CAMEO_XML>') or result.endswith('<CAMEO_XML/>'):
                print "send_request() encountered a problem but the result looks valid."
                break # Assume this means we got the result correctly
            else:
                continue # Didn't get something we recognize, try again if attempt < num_tries
        else:
            break # Success!  Break out of the num_tries loop

    if verbose: print '%s\n%s' % (result, DIV)
    return result

def send_shutdown_request(hostname=HOSTNAME, port=PORT):
    """
    Send a shutdown request to the ACCENT server.

    @param hostname: The hostname of the ACCENT HTTP server.
    @param port: The port on which the ACCENT HTTP server is listening.
    """
    print "Sending shutdown request to %s:%d" % (hostname, int(port))
    send_request('POST Shutdown', '', hostname, port)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", '--input_file', dest='input_file', help="Path to input batch file or input file", default = "")
    parser.add_option("-o", '--output_dir', dest='output_dir', help="Path to output directory", default = "")
    parser.add_option("-d", '--document_date', dest='document_date', help="Document date in YYYY-MM-DD format", default = None)
    opts, args = parser.parse_args()

    if len(args) == 2 and args[0] in ('process_batch_file', 'process_file', 'shutdown'):
        ip_address_regex = re.compile('[^:]+:\d+$')
        if ip_address_regex.match(args[1]):
            hostname, port = args[1].split(':')
        else:
            hostname, port = open(args[1]).read().strip().split(':')
    else:
        sys.exit("Usage is %s process_file|process_batch_file|shutdown server_info_file|host:port (-i <input_file> -o <output_dir> -d <document_date_YYYYMMDD>)" % sys.argv[0])
    
    if args[0] == 'process_batch_file' or args[0] == 'process_file':
        if len(opts.output_dir) == 0:
            print "You must specify an output directory with the -o option if you are processing documents."
            sys.exit(1)
        if not os.path.exists(opts.output_dir):
            try: 
                os.makedirs(opts.output_dir)
            except: 
                print "Couldn't make directory: " + opts.output_dir
                sys.exit(1)

    files = []
    if args[0] == 'process_batch_file':
        if not os.path.isfile(opts.input_file):
            print "When you use process_batch_file mode, you must specify a file with the -i parameter"
            sys.exit(1)
        files = [x.strip() for x in open(opts.input_file, 'rb').readlines()]
    if args[0] == 'process_file':
        if not os.path.isfile(opts.input_file):
            print "When you use process_file mode, you must specify a file with the -i parameter"
            sys.exit(1)
        files = [opts.input_file]

    if args[0] == 'process_batch_file' or args[0] == 'process_file':
        for index in range(len(files)):
            input_file = files[index]
            filename = os.path.basename(input_file)
            print "Processing file (%d of %d): %s" % (index + 1, len(files), filename)
            data = open(input_file, 'rb').read()
            doc = send_document(data, docid=filename, hostname=hostname, port=port, document_date=opts.document_date).split('\r\n\r\n', 1)[1]
            if len(filename) > 4 and (filename[-4:] == ".xml" or filename[-4:] == ".txt"):
                filename = filename[0:-4]
            file_path = os.path.join(opts.output_dir, "%s.cameo.xml" % filename)
            f = open(file_path, 'w')
            f.write(doc + "\n")
            f.close()
            print "Wrote: %s.cameo.xml" % filename
    

    elif args[0] == 'shutdown':
        send_shutdown_request(hostname, port)
