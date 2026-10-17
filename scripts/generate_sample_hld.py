"""
Script to generate realistic AUTOSAR High-Level Design (HLD) PDF documents for testing,
evaluation, and live demonstration of the AUTOSAR HLD Document Analysis Assistant.
"""

import os
import fitz  # PyMuPDF


def create_sample_hld_pdf(filename: str, version: str, is_v2_1: bool = False):
    doc = fitz.open()

    # Cover Page (Page 1)
    page1 = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 800)
    page1.insert_text(
        fitz.Point(72, 100),
        "AUTOSAR HIGH-LEVEL DESIGN SPECIFICATION",
        fontsize=18,
        fontname="helv",
    )
    page1.insert_text(
        fitz.Point(72, 130),
        "Subsystem: Advanced Electronic Brake Control System (EBCS)",
        fontsize=14,
        fontname="helv",
    )
    page1.insert_text(
        fitz.Point(72, 160),
        f"Document Version: {version}",
        fontsize=12,
        fontname="helv",
    )
    page1.insert_text(
        fitz.Point(72, 180),
        "Classification: Confidential - Automotive Engineering / Embedded Systems",
        fontsize=10,
        fontname="helv",
    )
    page1.insert_text(
        fitz.Point(72, 210),
        "Target Platform: AUTOSAR Classic Platform Release 4.4.0",
        fontsize=11,
        fontname="helv",
    )

    page1.insert_text(
        fitz.Point(72, 270),
        "1. Document Overview and Scope",
        fontsize=14,
        fontname="helv",
    )
    overview_text = (
        "This High-Level Design (HLD) specification defines the software architecture, "
        "Application Software Components (SWCs), ports, interfaces, signals, and functional "
        "data flows for the Electronic Brake Control System (EBCS). The system coordinates "
        "anti-lock braking (ABS), electronic stability control (ESC), and regenerative brake blending. "
        "All interfaces conform to AUTOSAR standard methodologies and ISO 26262 ASIL-D safety requirements.\n\n"
        "2. Architecture Baseline\n"
        "The software architecture decomposes into primary functional clusters: Sensor Ingestion SWCs, "
        "Algorithmic Computation SWCs, and Actuator Driver SWCs. Communication between components occurs "
        "via Virtual Functional Bus (VFB) Sender-Receiver and Client-Server interfaces."
    )
    page1.insert_textbox(fitz.Rect(72, 290, 520, 500), overview_text, fontsize=10)

    # Page 2: Component Architecture & Speed Processing
    page2 = doc.new_page()
    page2.insert_text(
        fitz.Point(72, 60),
        "3. Software Component Architecture Overview",
        fontsize=14,
        fontname="helv",
    )
    comp_text = (
        "The EBCS architecture comprises the following key Software Components (SWCs):\n"
        "- SpeedProcessingSWC: Ingests raw wheel speed pulse trains and computes filtered vehicle velocity.\n"
        "- BrakePedalSensorSWC: Measures driver brake pedal displacement and deceleration request force.\n"
        "- BrakeControlSWC: Calculates target brake pressure per wheel and traction slip limits.\n"
        "- HydraulicActuatorSWC: Directly drives electro-hydraulic valve coils and pump motor relays.\n"
        "- DiagnosticMonitorSWC: Performs ASIL-D plausibility checks and sensor fault isolation."
    )
    if is_v2_1:
        comp_text += (
            "\n- RegenBrakeCoordinatorSWC: (Added in v2.1) Arbitrates friction brake torque with "
            "electric powertrain regenerative braking."
        )
    page2.insert_textbox(fitz.Rect(72, 80, 520, 240), comp_text, fontsize=10)

    page2.insert_text(
        fitz.Point(72, 260),
        "4. Component Specification: SpeedProcessingSWC",
        fontsize=14,
        fontname="helv",
    )
    speed_swc_text = (
        "Section 4.1 Component Role\n"
        "SpeedProcessingSWC executes cyclically every 5ms on Task_Periodic_5ms. It samples the front-left, "
        "front-right, rear-left, and rear-right wheel pulse counters and calculates longitudinal vehicle velocity.\n\n"
        "Section 4.2 Port and Interface Definitions\n"
        "Component: SpeedProcessingSWC\n"
        "- Provide-Port: P_SpeedReceiver\n"
        "  Interface: VehicleSpeed_IF (SenderReceiverInterface)\n"
        "  Transmitted Signal: VehicleSpeed\n"
        "  Data Type: uint16 (Scaled 0.01 km/h per LSB, Range: 0 - 350.00 km/h)\n"
        "  Description: VehicleSpeed is received via port P_SpeedReceiver on component SpeedProcessingSWC "
        "and published to downstream subscribers including BrakeControlSWC and EngineControlSWC.\n\n"
        "- Require-Port: R_WheelSpeedSensor\n"
        "  Interface: WheelSpeedSensor_IF (SenderReceiverInterface)\n"
        "  Received Signal: RawWheelTicks\n"
        "  Data Type: uint32\n"
        "  Description: Raw magnetic hall sensor pulse transitions per millisecond."
    )
    page2.insert_textbox(fitz.Rect(72, 280, 520, 560), speed_swc_text, fontsize=10)

    # Page 3: Brake Control and Actuation
    page3 = doc.new_page()
    page3.insert_text(
        fitz.Point(72, 60),
        "5. Component Specification: BrakeControlSWC",
        fontsize=14,
        fontname="helv",
    )
    brake_swc_text = (
        "Section 5.1 Algorithmic Control Flow\n"
        "BrakeControlSWC operates cyclically every 10ms. It ingests VehicleSpeed from SpeedProcessingSWC "
        "and BrakePedalTravel from BrakePedalSensorSWC to determine primary braking pressure.\n\n"
        "Section 5.2 Ports and Signal Mappings\n"
        "- Require-Port: R_VehicleSpeedConsumer\n"
        "  Interface: VehicleSpeed_IF\n"
        "  Signal: VehicleSpeed\n"
        "  Data Type: uint16\n"
        "  Connection: Connected to SpeedProcessingSWC.P_SpeedReceiver via VFB assembly connector.\n\n"
        "- Require-Port: R_PedalPosition\n"
        "  Interface: PedalTravel_IF\n"
        "  Signal: DriverBrakeForce\n"
        "  Data Type: float32 (Unit: Newtons, Range: 0.0 - 1200.0 N)\n\n"
        "- Provide-Port: P_TargetBrakePressure\n"
        "  Interface: BrakePressure_IF (SenderReceiverInterface)\n"
        "  Transmitted Signal: TargetCylinderPressure\n"
        "  Data Type: float32 (Unit: Bar, Range: 0.0 - 250.0 Bar)"
    )
    if is_v2_1:
        brake_swc_text += (
            "\n\n- Provide-Port: P_RegenTorqueRequest (Added in v2.1)\n"
            "  Interface: RegenTorque_IF\n"
            "  Transmitted Signal: RegenTorqueDemand\n"
            "  Data Type: float32 (Unit: Nm, Range: -500.0 to 0.0 Nm)\n"
            "  Note: Connected to RegenBrakeCoordinatorSWC."
        )
    page3.insert_textbox(fitz.Rect(72, 80, 520, 500), brake_swc_text, fontsize=10)

    # Page 4: Actuator Interface & System Safety Validation
    page4 = doc.new_page()
    page4.insert_text(
        fitz.Point(72, 60),
        "6. Actuator Driver & Diagnostic Architecture",
        fontsize=14,
        fontname="helv",
    )
    actuator_text = (
        "Section 6.1 HydraulicActuatorSWC Details\n"
        "- Require-Port: R_CylinderPressureInput\n"
        "  Interface: BrakePressure_IF\n"
        "  Signal: TargetCylinderPressure\n"
        "  Data Type: float32\n"
        "- Provide-Port: P_ValvePWMOutput\n"
        "  Interface: ActuatorPWM_IF\n"
        "  Signal: CoilDutyCycle\n"
        "  Data Type: uint8 (Range: 0 - 100 %)\n\n"
        "Section 6.2 Diagnostic & Fault Isolation\n"
        "DiagnosticMonitorSWC continuously verifies whether signal plausibility bounds are satisfied. "
        "If VehicleSpeed deceleration exceeds 1.4g without corresponding TargetCylinderPressure build-up, "
        "an ISO 26262 Diagnostic Trouble Code (DTC_0x84A12) is latched into NvM (Non-Volatile Memory)."
    )
    if is_v2_1:
        actuator_text += (
            "\n\nSection 6.3 Test Inconsistency Injection (v2.1 Validation Scenario)\n"
            "- Unassigned Port: R_ExternalInertiaSensor on DiagnosticMonitorSWC remains unassigned "
            "without corresponding sensor SWC connector.\n"
            "- Dangling Signal: Signal WheelSlipRatio defined in SlipCalculation_IF has no active receiver component."
        )
    page4.insert_textbox(fitz.Rect(72, 80, 520, 520), actuator_text, fontsize=10)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc.save(filename)
    doc.close()
    print(f"Generated sample HLD PDF: {filename} ({version})")


if __name__ == "__main__":
    create_sample_hld_pdf(
        "data/sample_hlds/Brake_System_HLD_v2.0.pdf",
        version="v2.0.0",
        is_v2_1=False,
    )
    create_sample_hld_pdf(
        "data/sample_hlds/Brake_System_HLD_v2.1.pdf",
        version="v2.1.0",
        is_v2_1=True,
    )
