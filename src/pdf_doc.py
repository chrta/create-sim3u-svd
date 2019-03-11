import PyPDF2


class Chapter:
    def __init__(self, name, page):
        self.name = name
        self.page = [page]
        self.chapter = []

    def add_chapter(self, chapter):
        if self.chapter:
            self.chapter[-1].set_last_page(chapter.page[0])
        self.chapter.append(chapter)

    def set_last_page(self, page_no):
        if self.chapter:
            self.chapter[-1].set_last_page(page_no)
        if len(self.page) >= 2:
            raise Exception("Already last page set")
        if self.page[0] < page_no:
            self.page.append(page_no - 1)
        else:
            self.page.append(self.page[0])
        #print("Set last page of {} to {} (page {})".format(self.name, page_no, self.page))

    def get_chapter_pages(self, chapter_name):
        if self.name == chapter_name:
            return self.page
        for chapter in self.chapter:
            page = chapter.get_chapter_pages(chapter_name)
            if page:
                return page
        return None

    def get_pages_for_registers(self, peripheral_name):
        if ' Registers' in self.name and " " + peripheral_name in self.name:
            return self.page
        for chapter in self.chapter:
            page = chapter.get_pages_for_registers(peripheral_name)
            if page:
                return page
        return None

    def __str__(self):
        result = "Chapter '{}' pg. {}\n".format(self.name, self.page)
        for v in self.chapter:
            result += " " + v.__str__()
        return result


class Manual:
    def __init__(self):
        self.chapter = []

    def add_chapter(self, chapter):
        if self.chapter:
            self.chapter[-1].set_last_page(chapter.page[0])

        self.chapter.append(chapter)

    def get_chapter_pages(self, chapter_name):
        for chapter in self.chapter:
            page = chapter.get_chapter_pages(chapter_name)
            if page:
                return page
        return None

    def get_pages_for_registers(self, peripheral_name):
        for chapter in self.chapter:
            page = chapter.get_pages_for_registers(peripheral_name)
            if page:
                return page
        return None

    def __str__(self):
        result = "Manual:\n"
        for v in self.chapter:
            result += " " + v.__str__()
        result += "\n"
        return result


class Document:
    def __init__(self, filename):
        self.filename = filename

    def _store_toc(self, pdf, outlines, parent, indent=""):
        chapter = parent
        for o in outlines:
            if isinstance(o, PyPDF2.generic.Destination):
                #print("{}Destination {} pg. {}".format(indent, o.title, pdf.getDestinationPageNumber(o)))
                chapter = Chapter(o.title, pdf.getDestinationPageNumber(o) + 1)
                parent.add_chapter(chapter)
            elif isinstance(o, list):
                self._store_toc(pdf, o, chapter, indent + " ")
            else:
                raise Exception("Unexpected content in toc")

    def parse_toc(self):
        pdf = PyPDF2.PdfFileReader(open(self.filename, "rb"))
        print("{} has {} pages.".format(self.filename, pdf.getNumPages()))
        outlines = pdf.getOutlines()

        manual = Manual()
        self._store_toc(pdf, outlines, manual)
        return manual
