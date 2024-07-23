import micropython
import array


IMA_INDEX_TABLE = micropython.const((
  -1, -1, -1, -1, 2, 4, 6, 8,
  -1, -1, -1, -1, 2, 4, 6, 8
))

IMA_STEP_TABLE = micropython.const((
  7, 8, 9, 10, 11, 12, 13, 14, 16, 17,
  19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
  50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
  130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
  337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
  876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
  2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
  5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
  15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
))

ima_index_table = array.array("i", IMA_INDEX_TABLE)
ima_step_table = array.array("i", IMA_STEP_TABLE)


@micropython.viper
def encode(samples):
    encoded_samples = array.array("b", samples)
    _encoder_prevsample:int = 0
    _encoder_previndex:int = 0
    for i, sample in enumerate(samples):
        _state = _encoder(sample, _encoder_prevsample, _encoder_previndex)
        encoded_samples[i] = int(_state[0])
        _encoder_prevsample = int(_state[1])
        _encoder_previndex = int(_state[2])
    return encoded_samples


@micropython.viper
def _encoder(sample:int, prevsample:int, previndex:int):
    predsample:int = prevsample
    index:int = previndex
    step_table_ptr = ptr32(ima_step_table)
    step:int = step_table_ptr[index]

    # Compute difference between actual and predicted sample
    diff:int = sample - predsample
    code:int = 0
    if diff >= 0:
        code = 0
    else:
        code = 8
        diff = -diff

    # Quantize difference into 4-bit code using quantizer step size
    tempstep:int = step
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
    diffq:int = step >> 3
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
    index_table_ptr = ptr32(ima_index_table)
    index += index_table_ptr[code]

    # Correct quantizer step index overflow
    if index < 0:
        index = 0
    elif index > 88:
        index = 88

    return code & 0x0f, predsample, index


@micropython.viper
def decode(samples):
    decoded_samples = array.array("h", samples)
    _decoder_prevsample:int = 0
    _decoder_previndex:int = 0
    for i, sample in enumerate(samples):
        _state = _decoder(sample, _decoder_prevsample, _decoder_previndex)
        _decoder_prevsample = int(_state[0])
        _decoder_previndex = int(_state[1])
        decoded_samples[i] = _decoder_prevsample
    return decoded_samples


@micropython.viper
def _decoder(code:int, prevsample:int, previndex:int):
    predsample:int = prevsample
    index:int = previndex

    # Find quantizer step size from lookup table
    step_table_ptr = ptr32(ima_step_table)
    step:int = step_table_ptr[index]

    # Inverse quantize code into difference using quantizer step size
    diffq:int = step >> 3
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
    index_table_ptr = ptr32(ima_index_table)
    index += index_table_ptr[code]

    # Correct quantizer step index overflow
    if index < 0:
        index = 0
    elif index > 88:
        index = 88

    return predsample, index
