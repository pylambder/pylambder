"""Config loader. Global for now. Config file is loaded upon first use.
The file is key=value pairs, one per line."""


CONFIG_FILE = "local.config"


_config = None


def load(file):
    global _config
    with open(CONFIG_FILE, "r") as f:
        split = (line.split("=", 2) for line in f)
        skipped = (s for s in split if len(s) == 2)  # skip lines without '='
        stripped = ([w.strip() for w in words] for words in skipped)
        _config = _config if _config else dict()
        _config.update({k: v for [k, v] in stripped})


def get(key):
    global _config
    if _config is None:
        load(CONFIG_FILE)
    return _config[key]


def store(key, value):
    global _config
    if _config is None:
        _config = dict()
    _config[key] = value
