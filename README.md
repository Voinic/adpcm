# MicroPython IMA ADPCM Streaming Audio Compression

Proof of concept test exploring the aptX / ADPCM codecs used in streaming Bluetooth audio. Codec chosen for minimal reliance on floating point math - potentially suitable for embedded implementation, which would be the goal. Optimized for execution on MicroPython platform.

## Installation using MIP

```python
import mip
mip.install("github:Voinic/adpcm")
```

## Usage

```python
import array
from adpcm import encode, decode

audio = array.array('h', [-100, -50, 0, 50, 100])
print("Input audio:", audio)

# encode
audio_adpcm = encode(audio)
print("Encoded audio:", audio_adpcm)

# save or transmit audio_adpcm

# decode
_audio = decode(audio_adpcm)
print("Decoded audio:", _audio)
```

### Output

```text
Input audio: array('h', [-100, -50, 0, 50, 100])
Encoded audio: array('b', [15, 15, 4, 5, 3])
Decoded audio: array('h', [-11, -41, -3, 53, 105])
```
