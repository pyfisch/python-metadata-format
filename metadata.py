from collections import namedtuple
from io import StringIO
import logging

logger = logging.getLogger(__name__)

FOLD_SPACES = " " * 8
FOLD_PIPE = " " * 7 + "|"

Field = namedtuple("Field", ["name", "required", "multiple"])


def _normalize_field_name(name):
    return name.lower().replace("-", "_")


def _make_field(name, required=False, multiple=False):
    return (_normalize_field_name(name), Field(name, required, multiple))


class KeyValueStore:
    _fields = dict()
    _payload_key = None

    def __init__(self):
        self._data = dict()
        self._unknown_pairs = []

    def __str__(self):
        fp = StringIO()
        self.write(fp)
        return fp.getvalue()

    @classmethod
    def parse(cls, fp):
        obj = cls()
        line = fp.readline()
        while True:
            if line == "":
                # EOF reached
                break
            elif line == "\n":
                # end of headers reached
                break
            parts = line.split(":", maxsplit=1)
            if len(parts) != 2:
                raise Exception("Syntax error: invalid field.")
            key = parts[0]
            raw_value = [parts[1]]
            # handle line folding
            line = fp.readline()
            while line.startswith(" "):
                raw_value.append(line)
                line = fp.readline()
            value = obj._fold(key, raw_value)
            if value.strip() == "UNKNOWN":
                # Skip fields without value.
                continue
            # store key-value pair
            obj._store_pair(key, value)

        payload = fp.read()
        if payload.strip():
            if obj._payload_key is None:
                raise Exception("Only key-value pairs allowed, but no payload.")
            obj._store_pair(obj._payload_key, payload)
        obj._check()
        return obj

    def write(self, fp):
        self._check()
        result = []
        for name, field in self._fields.items():
            if not name in self._data:
                continue
            if name == self._payload_key:
                # Add the multiline payload later.
                continue
            if field.multiple:
                for value in self._data[name]:
                    fp.write(f"{field.name}: {value}\n")
            else:
                value = self._data[name]
                fp.write(f"{field.name}: {value}\n")
        fp.write("\n")
        if self._payload_key in self._data:
            fp.write(self._data[self._payload_key])

    def get_structured(self):
        # TODO: Should this use copy.deepcopy?
        return self._data

    def _fold(self, key, raw_value):
        return " ".join([line.strip() for line in raw_value])

    def _store_pair(self, key, value):
        normal_name = _normalize_field_name(key)
        if normal_name in self._fields:
            field = self._fields[normal_name]
            if field.multiple:
                self._data.setdefault(normal_name, []).append(value)
            else:
                if normal_name in self._data:
                    raise Exception(
                        f"Duplicate value for metadata field `{normal_name}`."
                    )
                self._data[normal_name] = value
        else:
            self._unknown_pairs.append((key, value))

    def _check(self):
        for name, field in self._fields.items():
            if field.required and name not in self._data:
                raise Exception(f"Required field `{field.name}` missing.")
            if name in self._data:
                assert not field.multiple or isinstance(self._data[name], list)
                assert field.multiple or isinstance(self._data[name], str)
        for (key, _value) in self._unknown_pairs:
            logger.info(f"Unknown field name `{key}`.")


class MetadataBase(KeyValueStore):
    __field_list = [
        _make_field("Metadata-Version", required=True),
        _make_field("Name", required=True),
        _make_field("Version", required=True),
        _make_field("Dynamic", multiple=True),
        _make_field("Platform", multiple=True),
        _make_field("Supported-Platform", multiple=True),
        _make_field("Summary"),
        _make_field("Summary"),
        _make_field("Description"),
        _make_field("Description-Content-Type"),
        _make_field("Keywords"),
        _make_field("Home-page"),
        _make_field("Download-URL"),
        _make_field("Author"),
        _make_field("Author-email"),
        _make_field("Maintainer"),
        _make_field("Maintainer-email"),
        _make_field("License"),
        _make_field("Classifier", multiple=True),
        _make_field("Requires-Dist", multiple=True),
        _make_field("Requires-Python"),
        _make_field("Requires-External", multiple=True),
        _make_field("Project-URL", multiple=True),
        _make_field("Provides-Extra", multiple=True),
        # rarely used fields
        _make_field("Provides-Dist", multiple=True),
        _make_field("Obsoletes-Dist", multiple=True),
    ]
    _fields = dict(__field_list)
    _payload_key = "description"

    def _fold(self, key, raw_value):
        if key.lower() != "description":
            return super()._fold(key, raw_value)
        # special handling for description field
        # https://packaging.python.org/specifications/core-metadata/#description
        value_lines = []
        for raw_line in raw_value:
            if raw_line.startswith(FOLD_SPACES):
                line = raw_line[8:]
            elif raw_line.startswith(FOLD_PIPE):
                line = raw_line[8:]
            else:
                # TODO: While this shouldn't happen in files, should it end in "\n"?
                line = raw_line.strip() + "\n"
            value_lines.append(line)
        return "".join(value_lines)

    def _check(self):
        super()._check()
        version = self._data["metadata_version"]
        if not version.startswith("1.") and not version.startswith("2."):
            raise Exception(f"METADATA file with version {version} is unsupported.")
        if version > "2.2":
            logger.warning(
                f"Encountered METADATA file with version {version}. "
                "The maximum supported version is 2.2."
            )


class Metadata(MetadataBase):
    pass


class PkgInfo(MetadataBase):
    pass


class Wheel(KeyValueStore):
    __field_list = [
        _make_field("Wheel-Version", required=True),
        _make_field("Generator"),
        _make_field("Root-Is-Purelib"),
        _make_field("Tag", multiple=True),
        _make_field("Build"),
    ]
    _fields = dict(__field_list)

    def _check(self):
        super()._check()
        wheel_version = self._data["wheel_version"]
        if not wheel_version.startswith("1."):
            raise Exception(f"WHEEL file with version {wheel_version} is unsupported.")
        elif wheel_version != "1.0":
            logger.warning(
                f"Encountered WHEEL file with version {wheel_version}. "
                "Only version 1.0 is supported right now."
            )
