import math
from collections import namedtuple

try:
    import cPickle as pickle
except ImportError:
    import pickle


############################################
###########         Entry        ###########
############################################
'''
Entry := an entry of the dictionary, containing the frequency of 
the token, the offset of the postings file, the size of the list
(of docIDs) corresponding inside the postings file
'''
Entry = namedtuple("Entry", ['frequency', 'offset', 'size'])


############################################
###########       Skiplist       ###########
############################################
class Skiplist(object):
    ''' a data structure that imitate a list of docIDs with skip pointers '''
    # read stored info from disk (I stored the string "orignal_index : jump_index"
    # at skip position when doing indexing)

    def __init__(self, set_in):
        lst = list(set_in)
        self.loaded_list = lst
        self.list = sorted(
            list(map(lambda x: int(x.split(":")[0]) if (isinstance(x, str)) else x, lst)))
        self.frequency = len(lst)
        self.step = int(math.floor(math.sqrt(self.frequency)))
        self.cursor = 0  # cursor position

    def __iter__(self):
        ''' Initialize, return itself '''
        self.cursor = 0
        return self

    def __next__(self, compare_id=None):

        # when there's no more elements
        if self.cursor >= self.frequency:
            raise StopIteration

        doc_id = self.loaded_list[self.cursor]
        if isinstance(doc_id, str):
            temp_id = int(doc_id.split(":")[1])
            doc_id = int(doc_id.split(":")[0])
            # check for potential skip
            if (self.frequency > 9) and compare_id:
                # obtain the value of the skip pointer
                if temp_id <= compare_id:  # if successful skip
                    self.cursor += self.step
                    doc_id = temp_id

        # increment cursor position prepare for next comparison
        self.cursor += 1
        return doc_id

    def get_length(self):
        return self.frequency

############################################
###########       Posting        ###########
############################################


class Posting(object):
    ''' a data structure that matches dictionary term and postings (docIDs) '''

    def __init__(self, dicionary, posting_file):
        self.dictionary = dicionary
        self.posting_file = posting_file

    def __getitem__(self, term):
        # implement of evaluation of self[key]
        ''' Return the associated Skiplist to a key or an empty Skiplist '''
        if term in self.dictionary:
            val = self.dictionary[term]  # Entry
            self.posting_file.seek(val.offset)
            return Skiplist(pickle.loads(self.posting_file.read(val.size)))
        else:
            return Skiplist([])


############################################
###########        BooleanTree          ###########
############################################
class BooleanTree(object):
    ''' a Boolean Tree represents a query '''

    def __init__(self, left, right, value):
        self.left = left    # left subtree
        self.right = right  # right subtree
        self.value = value  # an operand or an operator

    def eval(self, dictionary, file_list):
        ''' recursively evaluate the Boolean Tree to return a list of docs that results from the operations '''
        # @params:
        # dictionary: Postings dict
        # file_list: list of all the doc ids

        def left(): return self.left.eval(dictionary, file_list)

        def right(): return self.right.eval(dictionary, file_list)

        def sub_left(): return self.left.left.eval(dictionary, file_list)

        def sub_right(): return self.right.left.eval(dictionary, file_list)

        if self.value == "&":
            if self.left.value == '~' and self.right.value == '~':
                # ~a&~b <=> ~(a|b)
                return not_merge(or_merge(sub_left(), sub_right()), file_list)
            elif self.left.value == '~':  # ~a&b
                return and_not_merge(right(), sub_left())
            elif self.right.value == '~':  # a&~b
                return and_not_merge(left(), sub_right())
            return and_merge(left(), right())
        elif self.value == '|':
            if self.left.value == '~' and self.right.value == '~':
                # ~a|~b <=> ~(a&b)
                return not_merge(and_merge(sub_left(), sub_right()), file_list)
            return or_merge(left(), right())
        else:
            return not_merge(left(), file_list)


class Node(BooleanTree):
    def __init__(self, left, right, value):
        BooleanTree.__init__(self, left, right, value)


class Leaf(BooleanTree):
    def __init__(self, value):
        BooleanTree.__init__(self, None, None, value)

    def eval(self, dictionary, file_list):
        return dictionary[self.value]


def and_merge(l1, l2):
    # return l1 & l2
    out = []
    i1, i2 = iter(l1), iter(l2)
    try:
        e1, e2 = next(i1, False), next(i2, False)
        while e1 and e2:
            if e1 == e2:
                out.append(e1)
                e1, e2 = next(i1, False), next(i2, False)
            elif e1 < e2:
                e1 = i1.__next__(e2)
            else:
                e2 = i2.__next__(e1)
    except StopIteration:
        pass
    return Skiplist(out)


def and_not_merge(l1, l2):
    # return l1 & ~l2
    out = []
    i1, i2 = iter(l1.list), iter(l2.list)
    e1, e2 = next(i1, False), next(i2, False)
    while e1 and e2:
        if e1 == e2:
            e1, e2 = next(i1, False), next(i2, False)
        elif e1 < e2:
            out.append(e1)
            e1 = next(i1, False)
        else:
            e2 = next(i2, False)
    if e1:
        out.append(e1)
        for e in i1:
            out.append(e)
    return Skiplist(out)


def or_merge(l1, l2):
    # return l1 | l2
    out = []
    i1, i2 = iter(l1.list), iter(l2.list)
    e1, e2 = next(i1, False), next(i2, False)
    while e1 and e2:
        if e1 == e2:
            out.append(e1)
            e1, e2 = next(i1, False), next(i2, False)
        elif e1 < e2:
            out.append(e1)
            e1 = next(i1, False)
        else:
            out.append(e2)
            e2 = next(i2, False)
    if e1:
        out.append(e1)
        for e in i1:
            out.append(e)
    elif e2:
        out.append(e2)
        for e in i2:
            out.append(e)

    return Skiplist(out)


def not_merge(l1, l2):
    # return ~l1, where l2 is the list with all doc ids
    out = []
    i1, i2 = iter(l1.list), iter(l2.list)
    e1, e2 = next(i1, False), next(i2, False)
    while e1 and e2:
        if e1 == e2:
            e1, e2 = next(i1, False), next(i2, False)
        elif e1 < e2:
            e1 = next(i1, False)
        else:
            out.append(e2)
            e2 = next(i2, False)
    if e2:
        out.append(e2)
        for e in i2:
            out.append(e)
    return Skiplist(out)
