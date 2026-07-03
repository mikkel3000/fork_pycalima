========
PyCalima
========
Async protocol helpers for the
`Pax Calima® <http://www.pax.se/sv/produkt/calima/pax-calima-flakt>`_
bathroom fan created and sold by `Pax® <http://www.pax.se>`_

This module provides read and write helpers for the various GATT
characteristics of the Calima fan. It is transport-agnostic: callers
provide async read/write functions, so the same protocol code can be used
from Home Assistant's Bluetooth stack.

It no longer uses BluePy or opens Bluetooth connections itself.


Installation
----------
I did this on Raspberry Pi Zero W but it can be done on any computer which support BluePy (and has a bluetooth dongle).

Use uv for local development:

.. code:: shell

  uv run python -m unittest discover -s tests -v

Manual BLE smoke test:

.. code:: shell

  uv run --extra ble python examples/read_ble.py --list
  uv run --extra ble python examples/read_ble.py --name "PAX" --config

This test is read-first. It only writes to the fan if you explicitly pass
``--pin`` to authenticate:

.. code:: shell

  uv run --extra ble python examples/read_ble.py --name "PAX" --pin 123456 --config

Demo usage
----------
.. code:: python

  from pycalima import Calima

  fan = Calima(read_uuid, write_uuid)
  print(await fan.getAlias())

Command line tool
-----------------
The old BluePy command line tool has been removed from the supported API.

Debugging
-------------
Run the unit tests first; BLE-level logging belongs in the caller's
transport layer.

Documentation
-------------
A good readup introductory readup on BLE reverse engineering can be found
`here <https://medium.com/@urish/reverse-engineering-a-bluetooth-lightbulb-56580fcb7546#.9ltnsvdsn>`_.

Some badly structured details about the protocol can be found in the
`Characteristics file <characteristics.md>`_.

There is currently no documentation on the module yet, check the
Calima.py file to see available functions.

License
-------
See LICENSE file
