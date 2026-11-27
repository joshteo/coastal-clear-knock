[out:json][timeout:120];
(
  way["building"](-36.640,174.645,-36.595,174.705);
  way["highway"~"^(residential|tertiary|secondary|primary|unclassified|living_street|service|trunk|motorway)$"]["name"](-36.640,174.645,-36.595,174.705);
  node["addr:housenumber"](-36.640,174.645,-36.595,174.705);
);
out geom tags;
