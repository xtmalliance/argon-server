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

# Start states
class AcceptedState(State):
    def on_event(self, event):
        if event == 'operator_activates':
            return ActivatedState()
        elif event == 'operator_confirms_ended':
            return EndedState()
        elif event == 'ua_departs_early_late_outside_op_intent':
            return NonconformingState()

        return self

class ActivatedState(State):
    def on_event(self, event):
        if event == 'operator_confirms_ended':
            return EndedState()
        elif event == 'ua_exits_coordinated_op_intent':
            return NonconformingState()
        elif event == 'operator_initiates_contingent':
            return ContingentState()

        return self

class EndedState(State):
    def on_event(self, event):        
        return self
   
class NonconformingState(State):

    def on_event(self, event):
        if event == 'operator_return_to_coordinated_op_intent':
            return ActivatedState()
        elif event == 'operator_confirms_ended':
            return EndedState()
        elif event in ['timeout','operator_confirms_contingent']:
            return ContingentState()
        return self

class ContingentState(State):
    def on_event(self, event):
        if event == 'operator_confirms_ended':
            return EndedState()

        return self
# End states.

class FlightOperationStateMachine(object):
    def __init__(self, state= AcceptedState()):
        self.state = state
    def on_event(self, event):
        self.state = self.state.on_event(event)
