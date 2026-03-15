#include <pybind11/pybind11.h>
#include "autotopology.h"

namespace py = pybind11;

PYBIND11_MODULE(autotopology_cpp, m) {
    m.doc() = "AutoTopology C++ acceleration module";
    m.def("version", &autotopology::version, "Get C++ module version");
}
