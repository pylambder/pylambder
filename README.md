<deva name="logo"/>
<div align="center">
<a href="https://github.com/wgslr/pylambder" target="_blank">
<img src="logo.svg" alt="Logo" width="210" height="142"></img>
</a>
</div>

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/wgslr/pylambder/blob/master/LICENSE)

# pylambder

Easy way to run your python code as asynchronous tasks in AWS Lambda

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- Python 3.7
- AWS CLI
- SAM CLI

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

```bash
make test
```

### Unit tests

Unit tests are created using python's unitttest. They are in `test/` directory
and should be in files named `test_*.py`. This allows their autodiscovery.

### Linter

Install with `pip install -r dev-requirements.txt` or `pip install .[dev]` (this installs whole `pylambder`).

Run:
```bash
wgslr/pylambder$ pylint pylambder
```

The linter is configured in `pylintrc`. File `tox.ini` is also provided to configure `pep8` linter, used e.g. by Visual Studio Code.

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Artur Jopek** - [ajopek](https://github.com/ajopek)
* **Wojciech Geisler** - [wgslr](https://github.com/wgslr)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc

