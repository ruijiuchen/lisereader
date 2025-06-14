import numpy as np
from barion.amedata import *
from re import sub


class LISEreader:
    def __init__(self, filename):
        ame = AMEData()
        ame.init_ame_db
        self.ame_data = ame.ame_table
        self._read(filename)

    def _read(self, filename):
        import traceback
    
        with open(filename, encoding='latin1') as f:
            lines = f.readlines()
    
        for i, line in enumerate(lines):
            if '[Calculations]' in line:
                file_start = i + 1
                break
        else:
            raise ValueError("Missing [Calculations] section in file.")
    
        if lines[file_start].strip() == "":
            raise ValueError(f"Line {file_start + 1} is empty. Unexpected blank line after [Calculations].")
    
        self.centre_index = len(lines[file_start].split()) - 1
        self.data = []
    
        for lineno, line in enumerate(lines[file_start:], start=file_start + 1):
            if line.strip() == "":
                raise ValueError(f"Error: Empty line detected at line {lineno}.")
    
            try:
                line_clean = line.replace('+', '')
                tokens = line_clean.split()
    
                if len(tokens) <= self.centre_index:
                    raise ValueError(f"Line {lineno} has too few tokens: {line.strip()}")
    
                left_part = tokens[0:self.centre_index]
    
                right_tokens = line.replace('=', '').split()
                if len(right_tokens) <= self.centre_index:
                    raise ValueError(f"Line {lineno} missing '='-based right part: {line.strip()}")
    
                right_part = right_tokens[self.centre_index].split(',')
    
                self.data.append(left_part + right_part)
    
            except Exception as e:
                print(f"Failed to parse line {lineno}: {line.strip()}")
                traceback.print_exc()
                raise e

        
    def get_index(self, name):
        returned_queries = []
        for i, element in enumerate(self.data):
            if element[0] + '+' + element[1] == name:
                returned_queries.append(i)
            elif element[0] + element[1] + '+' == name:
                returned_queries.append(i)
        #print(" name = ",name ," ",returned_queries)   
        if len(returned_queries) == 1:
            return returned_queries[0]
        
        elif len(returned_queries) > 1:
            return returned_queries[0]
        
        else:
            print(element[0] + element[1] + '+')
            raise ValueError('get_index() returned nothing. Check formatting (e.g. \"80Kr35+\")')

    def get_info(self, name,verbose=True):
        try:
            index = self.get_index(name)
            from_lise = [list(map(int, self.data[index][1:self.centre_index])),
                         float(self.data[index][self.centre_index])]
            # 解析 name，格式如 '115Sb49+'
            match = re.match(r'^(\d+)([A-Za-z]+)(\d+)\+$', name)
            if not match:
                raise ValueError(f"Invalid ion name format: {name}")
            
            mass_number = int(match.group(1))  # '115'
            element = match.group(2)           # 'Sb'
            charge = int(match.group(3))       # '49'    
            # Match to AME data
            from_ame_candidates = [[line[6], line[5], line[4], line[3]]
                                   for line in self.ame_data
                                   if (element == line[6] and mass_number == line[5])]
    
            if not from_ame_candidates:
                if verbose:
                    raise ValueError(
                        f"⚠️ Nuclide {element}-{mass_number} not found in AME database.\n"
                        f"→ Please check if the AME data needs to be updated, or verify the formatting/spelling (e.g., 'Os' vs 'OS')."
                    )
    
            from_ame = from_ame_candidates[0]
            return from_ame + from_lise
    
        except Exception as e:
            if verbose:
                print(f"❌ Error in get_info({name}): {e}")
            raise


    def get_lise_all(self):
        data = np.array(self.data)
        return np.transpose([data[:, 0], data[:, 5], data[:, 6]])

    def get_info_all(self,verbose=True):
        result = []
        for line in self.data:
            if len(line) >= 2:
                ion_name = line[0]  + line[1] + '+'
                try:
                    info = self.get_info(ion_name, verbose=verbose)
                    result.append(info)
                except Exception as e:
                    if verbose:
                        print(f"⚠️ Skipping {ion_name} due to error: {e}")
        return result    

    def get_info_specific(self,param_index_list):
        return_list = [[LISEreader.float_check(line[i]) for i in param_index_list]
                       for line in self.data]
        return return_list

    def get_yield_sorted(self):
        name_yield = [[str(line[0]) + '+' + str(line[1]), LISEreader.float_check(line[7])] for line in self.data]
        sorted_by_yield = sorted(name_yield, key=lambda x: x[1])[::-1]
        return sorted_by_yield
        
    @staticmethod
    def float_check(value): #returns float if not string
        if value.replace('.','').replace('e-','').replace('e+','').isdigit():
            return float(value)
        else:
            return value
        
# ================== testing =====================

def test1():
    print(f"get_info(\'80Kr\'): {lise_data.get_info('80Kr')}")
    
def test2():
    print(f'get_info_all() snippet[:3]: {lise_data.get_info_all()[:3]}')
    
def test3():
    print(f"get_info_specific([0,1,10]) snippet[:3]: {lise_data.get_info_specific([0,1,10])[:3]}")

if __name__ == '__main__':
    filename = 'E143_TEline-ESR-72Ge.lpp'
    lise_data = LISEreader(filename)
    try:
        test1()
        test2()
        test3()
    except:
        raise
