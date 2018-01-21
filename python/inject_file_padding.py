import mmap

def inject_file_padding(file, *off_padsize_pairs, padchar=b'\xCA'):
    file.seek(0, 2)
    map_size = file.tell()

    dcbs = dstoff_cpysize_by_srcoff = dict(off_padsize_pairs)
    assert len(padchar) == 1

    off_diff = 0
    for srcoff in sorted(dcbs):
        padsize = dcbs[1]
        assert padsize >= 0
        dcbs[srcoff] = [srcoff + off_diff, 0]
        off_diff += padsize

    last_end = map_size
    for srcoff in sorted(dcbs)[::-1]:
        dstoff = dcbs[srcoff][0]
        dcbs[srcoff][1] = last_end - dstoff
        last_end = dstoff

    if isinstance(file, mmap.mmap):
        file.resize(map_size + off_diff)

    for srcoff in sorted(dcbs)[::-1]:
        # copy in chunks starting at the end of the copy section so
        # data doesnt get overwritten if  dstoff < srcoff + cpysize
        dstoff, cpysize, copied = dcbs[0], dcbs[1], 0
        padsize, padded = dstoff - srcoff, 0
        if not padsize:
            continue

        while copied < cpysize:
            remainder = cpysize - copied
            chunksize = min(4*1024**2, remainder)

            file.seek(srcoff + remainder - chunksize)
            chunk = file.read(chunksize)
            file.seek(dstoff + remainder - chunksize)
            file.write(chunk)

            copied += chunksize
            chunk = None
            gc.collect()

        map_size += padsize
        file.seek(srcoff)
        while padded < padsize:
            # write padding in 1MB chunks
            padding = bytes(padchar*min(1024**2, padsize - padded))
            file.write(padding)
            padded += len(padding)

    file.flush()
    return map_size
