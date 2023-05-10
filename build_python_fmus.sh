cd python/test_scenario
pythonfmu build -f lv_grid_fmu.py
pythonfmu build -f controller_tap.py
cd ../..
mv python/test_scenario/*fmu fmus/
