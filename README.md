# sachannelupdate


## Utility for pushing updates to Spamassassin update channels

sachannelupdate is a utility for pushing updates to Spamassassin update channels.
It is used to [publish](https://wiki.apache.org/spamassassin/PublishingRuleUpdates)
rules to a custom Spamassassin sa-update channel.

[![Build Status](https://travis-ci.org/akissa/sachannelupdate.svg)](https://travis-ci.org/akissa/sachannelupdate)
[![Code Climate](https://codeclimate.com/github/akissa/sachannelupdate/badges/gpa.svg)](https://codeclimate.com/github/akissa/sachannelupdate)
[![codecov.io](https://codecov.io/github/akissa/sachannelupdate/coverage.svg?branch=master)](https://codecov.io/github/akissa/sachannelupdate?branch=master)


## Installation

Install from PyPi

    pip install sachannelupdate

Install from Githib

    git clone https://github.com/akissa/sachannelupdate.git
    cd sachannelupdate
    python setup.py install

## Usage

sachannelupdate can be used from within python code or using the commandline
utility updatesachannel.

## Python usage

TODO

## Command line usage

```bash
updatesachannel -h
Usage: updatesachannel [options]

Options:
  -h, --help            show this help message and exit
  -c FILENAME, --config=FILENAME
                        configuration file
  -d, --delete          Deletes existing environment
```

## Contributing

1. Fork it (https://github.com/akissa/sachannelupdate/fork)
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request


## License

All code is licensed under the
[AGPLv3+ License](https://github.com/akissa/sachannelupdate/blob/master/LICENSE).
