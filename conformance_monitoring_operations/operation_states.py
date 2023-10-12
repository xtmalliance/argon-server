from enum import Enum


class OperationEvent(Enum):
    DSS_ACCEPTS = "dss_accepts"
    OPERATOR_ACTIVATES = "operator_activates"
    OPERATOR_CONFIRMS_ENDED = "operator_confirms_ended"
    UA_DEPARTS_EARLY_LATE_OUTSIDE_OP_INTENT = "ua_departs_early_late_outside_op_intent"
    UA_EXITS_COORDINATED_OP_INTENT = "ua_exits_coordinated_op_intent"
    OPERATOR_INITIATES_CONTINGENT = "operator_initiates_contingent"
    OPERATOR_RETURN_TO_COORDINATED_OP_INTENT = (
        "operator_return_to_coordinated_op_intent"
    )
    OPERATOR_CONFIRMS_CONTINGENT = "operator_confirms_contingent"
    TIMEOUT = "timeout"


class State(object):
    """
    A object to hold state transitions as defined in the ASTM F3548-21 standard
    Source: https://dev.to/karn/building-a-simple-state-machine-in-python
    """

    def __init__(self):
        print("Processing current state:%s" % str(self))

    def get_value(self):
        return self._value

    def on_event(self, event):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


class ProcessingNotSubmittedToDss(State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.DSS_ACCEPTS:
            return AcceptedState()
        return self


class AcceptedState(State):
    def on_event(self, event: OperationEvent):
        match event:
            case OperationEvent.OPERATOR_ACTIVATES:
                return ActivatedState()
            case OperationEvent.OPERATOR_CONFIRMS_ENDED:
                return EndedState()
            case OperationEvent.UA_DEPARTS_EARLY_LATE_OUTSIDE_OP_INTENT:
                return NonconformingState()
            case _:
                return self


class ActivatedState(State):
    def on_event(self, event: OperationEvent):
        match event:
            case OperationEvent.OPERATOR_CONFIRMS_ENDED:
                return EndedState()
            case OperationEvent.UA_EXITS_COORDINATED_OP_INTENT:
                return NonconformingState()
            case OperationEvent.OPERATOR_INITIATES_CONTINGENT:
                return ContingentState()
            case _:
                return self


class EndedState(State):
    def on_event(self, event: OperationEvent):
        return self


# Use this when the state number is not within the given standard numbers. eg : -1,999
class InvalidState(State):
    def on_event(self, event: OperationEvent):
        return self


class NonconformingState(State):
    def on_event(self, event: OperationEvent):
        match event:
            case OperationEvent.OPERATOR_RETURN_TO_COORDINATED_OP_INTENT:
                return ActivatedState()
            case OperationEvent.OPERATOR_CONFIRMS_ENDED:
                return EndedState()
            case OperationEvent.TIMEOUT | OperationEvent.OPERATOR_CONFIRMS_CONTINGENT:
                return ContingentState()

            case _:
                return self


class ContingentState(State):
    def on_event(self, event: OperationEvent):
        if event == OperationEvent.OPERATOR_CONFIRMS_ENDED:
            return EndedState()

        return self


class FlightOperationStateMachine(object):
    def __init__(self, state: int = 1):
        s = _match_state(state)
        self.state = s

    def on_event(self, event: OperationEvent):
        self.state = self.state.on_event(event)


def _match_state(status: int):
    match status:
        case 0:
            return ProcessingNotSubmittedToDss()
        case 1:
            return AcceptedState()
        case 2:
            return ActivatedState()
        case 3:
            return NonconformingState()
        case 4:
            return ContingentState()
        case 5:
            return EndedState()
        case _:
            return InvalidState()


def get_status(state: State) -> int:
    match state:
        case ProcessingNotSubmittedToDss():
            return 0
        case AcceptedState():
            return 1
        case ActivatedState():
            return 2
        case NonconformingState():
            return 3
        case ContingentState():
            return 4
        case EndedState():
            return 5
        case _:
            return -1
