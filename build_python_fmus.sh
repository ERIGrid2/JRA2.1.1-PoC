cd python/test_scenario
python lv_grid_pp.py
pythonfmu build -f lv_grid_fmu.py
pythonfmu build -f controller_tap.py
cd ../..
mv python/test_scenario/*fmu fmus/

cd python/jra1.2_scenario
python lv_grid_jra12_pp.py
pythonfmu build -f lv_grid_jra12_fmu.py
pythonfmu build -f controller_voltage.py
cd ../..
mv python/jra1.2_scenario/*fmu fmus/
