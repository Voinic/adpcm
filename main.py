import struct
import wave

ima_index_table = [
  -1, -1, -1, -1, 2, 4, 6, 8,
  -1, -1, -1, -1, 2, 4, 6, 8
]

ima_step_table = [
  7, 8, 9, 10, 11, 12, 13, 14, 16, 17,
  19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
  50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
  130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
  337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
  876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
  2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
  5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
  15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
]


def audio_reader():
    with wave.open("input.wav", "rb") as w:
        samples = []
        print(w.getparams())
        # for i in range(10):
        while True:
            samp = w.readframes(1)
            try:
                samples.append(struct.unpack("<h", samp)[0])
            except struct.error:
                break
        return samples


def audio_writer(samples, title):
    with wave.open(title, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        for samp in samples:
            w.writeframesraw(struct.pack("<h", samp))


def encoder(samples):
    encoded_samples = []
    _encoder_prevsample = 0
    _encoder_previndex = 0
    for sample in samples:
        _code, _encoder_prevsample, _encoder_previndex = _encoder(sample, _encoder_prevsample, _encoder_previndex)
        encoded_samples.append(_code)
    return encoded_samples


def _encoder(sample, prevsample, previndex):
    predsample = prevsample
    index = previndex
    step = ima_step_table[index]

    # Compute difference between actual and predicted sample
    diff = sample - predsample
    if diff >= 0:
        code = 0
    else:
        code = 8
        diff = -diff

    # Quantize difference into 4-bit code using quantizer step size
    tempstep = step
    if diff >= tempstep:
        code |= 4
        diff -= tempstep
    tempstep >>= 1
    if diff >= tempstep:
        code |= 2
        diff -= tempstep
    tempstep >>= 1
    if diff >= tempstep:
        code |= 1

    # Inverse quantize code into predicted difference using quantizer step size
    diffq = step >> 3
    if code & 4:
        diffq += step
    if code & 2:
        diffq += step >> 1
    if code & 1:
        diffq += step >> 2

    # Fixed predictor computes new prediction by adding old prediction to predicted difference
    if code & 8:
        predsample -= diffq
    else:
        predsample += diffq

    # Correct overflow
    if predsample > 32767:
        predsample = 32767
    elif predsample < -32768:
        predsample = -32768

    # Get new quantizer step-size index by adding old index to table lookup
    index += ima_index_table[code]

    # Correct quantizer step index overflow
    if index < 0:
        index = 0
    elif index > 88:
        index = 88

    return code & 0x0f, predsample, index


def decoder(samples):
    decoded_samples = []
    _decoder_prevsample = 0
    _decoder_previndex = 0
    for i, sample in enumerate(samples):
        if (i % 50000) == 0:
            # Packet loss simulation
            continue
        _decoder_prevsample, _decoder_previndex = _decoder(sample, _decoder_prevsample, _decoder_previndex)
        decoded_samples.append(_decoder_prevsample)
    return decoded_samples


def _decoder(code, prevsample, previndex):
    predsample = prevsample
    index = previndex

    # Find quantizer step size from lookup table
    step = ima_step_table[index]

    # Inverse quantize code into difference using quantizer step size
    diffq = step >> 3
    if code & 4:
        diffq += step
    if code & 2:
        diffq += step >> 1
    if code & 1:
        diffq += step >> 2

    # Add difference to predicted sample
    if code & 8:
        predsample -= diffq
    else:
        predsample += diffq

    # Correct overflow
    if predsample > 32767:
        predsample = 32767
    elif predsample < -32768:
        predsample = -32768

    # Get new quantizer step-size index by adding old index to table lookup
    index += ima_index_table[code]

    # Correct quantizer step index overflow
    if index < 0:
        index = 0
    elif index > 88:
        index = 88

    return predsample, index


if __name__ == "__main__":
    _samples = audio_reader()
    encoded = encoder(_samples)
    decoded = decoder(encoded)
    audio_writer(decoded, "output.wav")
