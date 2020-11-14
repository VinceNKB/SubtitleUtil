#!/usr/bin/env python3
# coding=utf-8

import os
import re
from datetime import datetime
from datetime import timedelta

class Parser:
    def __init__(self):
        self.tag_rex = "^\[(.+)\]$"
        self.sections_name = []
        self.sections = {}
        self.file_path = ""
        self.file_name = ""
        self.file_dir = ""
        self.ext = ""
        self.events_sec = None

    def FromText(self, lines):
        # line: list of string
        i = 0
        current_section = None
        for line in lines:
            current_line = line.strip()
            header = self.GetHeader(current_line)
            if header:
                if header not in self.sections:
                    self.sections[header] = Section(header)
                    self.sections_name.append(header)
                current_section = self.sections[header]
            elif len(lines[i]) > 0:
                current_section.Content.append(current_line)
            else:
                pass

        self.events_sec = Events(self.sections["Events"])


    def FromFile(self, file_path):
        if not os.path.exists(file_path):
            raise Exception("File not exists")

        self.file_path = file_path
        self.file_dir = os.path.dirname(file_path)
        name = os.path.basename(file_path)
        if name.endswith("ass"):
            self.ext = "ass"
            self.file_name = name[:-3]
        else:
            raise Exception("File type not supported")

        texts = []
        with open(file_path, "r", encoding="utf-8-sig") as read_file:
            for line in read_file:
                texts.append(line.strip())

        self.FromText(texts)

    def ToFile(self, file_path = None):
        if not file_path:
            file_path = os.path.join(self.file_dir, "%s%s.%s" % (self.file_name, "edited", self.ext))

        if self.events_sec:
            self.sections["Events"].Content = self.events_sec.to_string_list()

        with open(file_path, "w", encoding="utf-8") as write_file:
            for sec_name in self.sections_name:
                write_file.write("[%s]\n" % sec_name)
                for line in self.sections[sec_name].Content:
                    write_file.write("%s\n" % line)
                write_file.write("\n")

    def GetHeader(self,line):
        m = re.match(self.tag_rex, line)
        if m:
            return m.group(1)
        else:
            return None

    def shift_time_in_event(self, isAdd, hours, minutes, seconds, microseconds):
        delta = timedelta(hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)

        for e in self.events_sec.event_list:
            e.update_startAndEnd(isAdd, delta)

class Section:
    def __init__(self, header = ""):
        self.Header = header
        self.Content = []

class Events:
    def __init__(self, section):
        [_, formats_text] = (section.Content[0]).strip().split(":", 1)
        self.formats = [f.strip() for f in formats_text.split(",")]
        self.event_list = []
        for item in section.Content[1:]:
            if len(item) > 0:
                self.event_list.append(Event(self.formats, item))

    def to_string_list(self, formats_list = None):
        if not formats_list:
            formats_list = self.formats

        texts = []
        texts.append("Format: "+ ", ".join(formats_list))
        for e in self.event_list:
            texts.append("%s: %s" % (e.event_type, ",".join([e.data[f] for f in formats_list])))

        return texts


class Event:
    def __init__(self, formats, content):
        # formats: [Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text]
        # content: Dialogue: 0,0:05:57.30,0:06:00.72,*Default,NTP,0,0,0,,.....
        [event_type, details] = content.strip().split(":", 1)
        self.event_type = event_type
        detail_list = details.strip().split(",", len(formats)-1)
        self.data = {}
        for i in range(len(formats)):
            self.data[formats[i]] = detail_list[i]

        self.allow_time_shift = "Start" in formats and "End" in formats

    def update_startAndEnd(self, isAdd, delta):
        if not self.allow_time_shift:
            raise Exception("No Start or End time")

        if isAdd:
            self.data["Start"] = (datetime.strptime(self.data["Start"], "%H:%M:%S.%f") + delta).strftime("%H:%M:%S.%f")[:-4]
            self.data["End"] = (datetime.strptime(self.data["End"], "%H:%M:%S.%f") + delta).strftime("%H:%M:%S.%f")[:-4]
        else:
            self.data["Start"] = (datetime.strptime(self.data["Start"], "%H:%M:%S.%f") - delta).strftime("%H:%M:%S.%f")[:-4]
            self.data["End"] = (datetime.strptime(self.data["End"], "%H:%M:%S.%f") - delta).strftime("%H:%M:%S.%f")[:-4]

if __name__ == "__main__":
    parser = Parser()
    parser.FromFile("something.ass")
    parser.shift_time_in_event(True, 0, 0, 32, 0)
    parser.ToFile()