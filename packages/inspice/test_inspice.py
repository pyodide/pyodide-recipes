from pytest_pyodide import run_in_pyodide


@run_in_pyodide(packages=["inspice"])
def test_inspice(selenium):
    """Test basic ngspice analog simulation"""
    from InSpice.Spice.NgSpice.Shared import NgSpiceShared

    # Use new_instance() singleton factory to avoid cffi duplicate declarations
    ngspice = NgSpiceShared.new_instance()

    circuit = """
    .title Voltage Multiplier

    .SUBCKT 1N4148 1 2
    *
    R1 1 2 5.827E+9
    D1 1 2 1N4148
    *
    .MODEL 1N4148 D
    + IS = 4.352E-9
    + N = 1.906
    + BV = 110
    + IBV = 0.0001
    + RS = 0.6458
    + CJO = 7.048E-13
    + VJ = 0.869
    + M = 0.03
    + FC = 0.5
    + TT = 3.48E-9
    .ENDS

    Vinput in 0 DC 0V AC 1V SIN(0V 10V 50Hz 0s 0Hz)
    C0 in 1 1mF
    X0 1 0 1N4148
    C1 0 2 1mF
    X1 2 1 1N4148
    C2 1 3 1mF
    X2 3 2 1N4148
    C3 2 4 1mF
    X3 4 3 1N4148
    C4 3 5 1mF
    X4 5 4 1N4148
    R1 5 6 1MegOhm
    .options TEMP = 25°C
    .options TNOM = 25°C
    .options filetype = binary
    .options NOINIT
    .ic
    .tran 0.0001s 0.4s 0s
    .end
    """
    ngspice.load_circuit(circuit)
    ngspice.run()
    plot = ngspice.plot(simulation=None, plot_name=ngspice.last_plot)
    assert "V(6)" in plot


@run_in_pyodide(packages=["inspice"])
def test_inspice_xspice(selenium):
    """Test XSPICE mixed-signal simulation with ADC bridge"""
    from InSpice.Spice.NgSpice.Shared import NgSpiceShared

    # Use new_instance() singleton factory - reuses same instance as test_inspice
    # This avoids cffi duplicate declaration errors with global ffi.cdef()
    ngspice = NgSpiceShared.new_instance()

    # Load XSPICE code model
    ngspice.exec_command("codemodel /usr/lib/ngspice/digital.cm")

    # Simple XSPICE test: Analog sine -> ADC bridge
    # NOTE: lowercase 'a' for XSPICE device instance names
    circuit = """
    .title XSPICE ADC Bridge Test

    vdummy dummy 0 DC=0

    * Analog sine wave source
    vin in 0 SIN(0 2.5 1e6 0 0)

    * ADC bridge: Convert analog to digital
    aadc [in] [dout] adc1
    .model adc1 adc_bridge(in_low = 1.0 in_high = 2.0)

    * Resistor to complete circuit
    R1 in 0 1MEG

    .tran 0.01us 5us
    .end
    """

    ngspice.load_circuit(circuit)
    ngspice.run()
    plot = ngspice.plot(simulation=None, plot_name=ngspice.last_plot)

    # Verify analog input exists (proves simulation ran)
    # Note: plot keys are lowercase node names without V() prefix
    assert "in" in plot
