# MTEX sample data

The sample data of [MTEX](https://github.com/mtex-toolbox/mtex) and its ports to Julia and
Python: EBSD maps, 3D volumes, pole figures, ODFs, orientations, tensors, crystal files. The
documentation of every port reads its examples from here.

## Layout

The folders are those of MATLAB MTEX's `data/`, so a path is the same in every port and a
local copy of that folder serves as well.

| file | what it is |
|---|---|
| `manifest.json` | every file with its sha256, size and URL, and every data set; generated |
| `datasets.json` | the data sets: name, type, description, files; edited by hand |
| `large.json` | the files of 50 MiB or more, attached to a release instead of committed; generated |
| `tools/manifest.py` | writes and checks the manifest |

A data set is what `mtexdata(name)` loads. How a port turns the files into an object (the
phases, the Euler correction, the crop a documentation page applies) is the port's recipe
and stays in the port.

## Using it from a port

A port pins a tag. It copies `manifest.json` of that tag, or generates its own manifest
from it, and downloads a file from the URL given there, checking the sha256. The
committed files are served as
`https://raw.githubusercontent.com/mtex-toolbox/mtex-data/<tag>/<path>`, the large ones as
`https://github.com/mtex-toolbox/mtex-data/releases/download/<release>/<name>`, the release
being the one the file was first attached to.

## Adding or changing data

1. Put the file in its folder and name it in `datasets.json` if it belongs to a data set.
2. Run `python tools/manifest.py <next tag>` and `python tools/manifest.py --check`.
3. Commit, tag, push the tag, and create the release of the tag with the files that
   `large.json` lists under it attached.

A file is never changed under an existing path: a tag, once pushed, is what ports pin.

## Licence

The collection is licensed under [CC BY 4.0](LICENSE). Some files are sample files of
instrument vendors or come from published studies; please cite the source a documentation
page gives when you use them in a publication.
