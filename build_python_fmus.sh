cd python
pythonfmu build -f lv_grid_fmu.py
pythonfmu build -f controller_tap.py
cd ..
cp python/*fmu fmus/
