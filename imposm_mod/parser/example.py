# Copyright 2011 Omniscale GmbH & Co. KG
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import multiprocessing
from imposm_mod.parser import OSMParser
from collections import defaultdict

def ways_tag_filter(tags):
    for key in tags.keys():
        if key != 'highway':
          del tags[key]

if __name__ == '__main__':
    
    class Counter(object):
        def __init__(self):
            self.ways_counter = 0
            self.relations_counter = 0
        def incr_ways(self, ways):
            self.ways_counter += len([id for id,tags,ref in ways if 'highway' in tags])
        def incr_relations(self, relations):
            self.relations_counter += len(relations)
            
    counter = Counter()
    p = OSMParser(ways_callback=counter.incr_ways, relations_callback=counter.incr_relations,
        ways_tag_filter=ways_tag_filter)
    p.parse(sys.argv[1])
    print counter.ways_counter, counter.relations_counter
