# offline_eval.py -- the SWE-bench harness with its containers cut off from
# the network: each container that the Docker SDK creates on the harness's
# behalf gets network_mode="none". Images are still pulled by the daemon.
# usage: python3 offline_eval.py (the arguments of run_evaluation)
import runpy

from docker.models.containers import ContainerCollection

create = ContainerCollection.create


def create_offline(self, *args, **kwargs):
    return create(self, *args, network_mode="none", **kwargs)


ContainerCollection.create = create_offline
runpy.run_module("swebench.harness.run_evaluation", run_name="__main__",
                 alter_sys=True)
