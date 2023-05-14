mkdir -p fmus
cd fmi3
mkdir build
cd build
cmake ..
make
cd ../../
cp fmi3/build/dist/*fmu fmus/
