if os.getenv("FLEE_TYPE_CHECK") is not None and os.environ["FLEE_TYPE_CHECK"].lower() == "true":
    from beartype import beartype as check_args_type
else:
    def check_args_type(func):
        return func



@check_args_type
def getEndPointScore(link) -> float:
  """
  Summary

  Args:
    link (Link): Description

  Returns:
    float: Description
  """
  # print(link.endpoint.name, link.endpoint.scores)
  return link.endpoint.scores[1]


@check_args_type
def calculateLinkWeight(
  link: Link,
  prior_distance: float,
  origin_names: List[str],
  step: int,
  time: int,
  debug: bool = False,
) -> float:
  """
  Calculates Link Weights recursively based on awareness level.
  Loops are avoided.

  Args:
  a: agent (TODO: make obsolete?_
  link (Link): Description
  prior_distance (float): Description
  origin_names (List[str]): Description
  step (int): Description
  time (int): Description
  debug (bool, optional): Description
  """
  weight = float(getEndPointScore(link=link)
          / float(SimulationSettings.move_rules["Softening"] + link.get_distance() + prior_distance)) 
          * link.endpoint.getCapMultiplier(numOnLink=int(link.numAgents))

  if debug:
    print("step {}, dest {}, dist {}, prior_dist {}, score {}, weight {}".format(
        step,
        link.endpoint.name,
        link.get_distance(),
        prior_distance,
        getEndPointScore(link=link),
        weight)
    )

  if SimulationSettings.move_rules["AwarenessLevel"] > step:
    # Traverse the tree one step further.
    for e in link.endpoint.links:
      if e.endpoint.name in origin_names:
        # Link points back to an origin, so ignore.
        pass
      else:
        weight = max(
          weight,
          calculateLinkWeight(a,
              link=e,
              prior_distance=prior_distance + link.get_distance(),
              origin_names=origin_names + [link.endpoint.name],
              step=step + 1,
              time=time,
              debug=debug,
              ),
          )

  if debug:
    print("step {}, total weight returned {}".format(step, weight))
  return weight


@check_args_type
def normalizeWeights(weights) -> list:
  """
  Summary

  Args:
    weights (List[float]): Description

  Returns:
    list: Description
  """
  if np.sum(weights) > 0.0:
    weights /= np.sum(weights)
  else:  # if all have zero weight, then we do equal weighting.
    weights += 1.0 / float(len(weights))
  return weights.tolist()



@check_args_type
def chooseFromWeights(weights, linklist):
  """
  Summary

  Args:
    weights (List[float]): Description
    linklist (List[Link]): Description

  Returns:
    float: Description
  """
  if len(weights) == 0:
    return None

  weights = normalizeWeights(weights=weights)
  result = random.choices(linklist, weights=weights)
  return result[0]


@check_args_type
def selectRoute(a, time: int, debug: bool = False):
  """
  Summary

  Args:
  a: Agent
  time (int): Description
  debug (bool, optional): Description

  Returns:
  int: Description
  """
  linklen = len(a.location.links)
  weights = np.zeros(linklen)

  if SimulationSettings.move_rules["AwarenessLevel"] == 0:
    return np.random.randint(0, linklen)

  for k, e in enumerate(a.location.links):
    weights[k] = calculateLinkWeight(
         link=e,
         prior_distance=0.0,
         origin_names=[a.location.name],
         step=1,
         time=time,
         debug=debug,
    )

  return chooseFromWeights(weights=weights, linklist=a.location.links)

