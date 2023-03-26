from py2neo import *
import os 
import json


class Encyclopedia():
    def __init__(self) -> None:
        self.graph = Graph('bolt://localhost:7687', auth = ('neo4j', 'Wsh021006'))
        
        # 植物的性状
        self.charas = ["生活型", "高度", "叶片形状", "叶片颜色", "花朵形状", "花朵颜色", "果实形状", "果实颜色",
                       "树皮形状", "树皮颜色",
                       "温度", "光照", "保护和改造环境价值", "药用价值", "食用价值", "工业价值", "栽培价值", 
                       "抗逆性", "病害名称", "虫害名称"]
        # self.node_basic_attris = ['中文名', '别名', '描述']
        self.node_basic_attris = ['中文名', '别名']
        self.distri_attris = ['省份', '地区', '国家']
        self.family_attris = ['界', '门', '纲', '目', '科', '属']

    def attri_chara_template(self):
        template_dict = {}
        for attri in self.node_basic_attris:
            template_dict[attri] = '它的{0}为'.format(attri)
        for chara in self.charas:
            if '颜色' in chara or '形状' in chara:
                template_dict[chara] = '它的{0}主要有'.format(chara)
            elif '高度' in chara:
                template_dict[chara] = '该种植物的{0}一般为'.format(chara)
            elif '温度' in chara or '光照' in chara:
                template_dict[chara] = '这种植物生长的{0}条件为'.format(chara)
            elif '价值' in chara:
                template_dict[chara] = '在{0}方面，其可以用于或用作'.format(chara)
            elif '害' in chara:
                template_dict[chara] = '其易得的{0}是'.format(chara)
            elif '抗逆性' in chara:
                template_dict[chara] = '这种植物的抗逆特性为'
            elif '生活型' in chara:
                template_dict[chara] = '它的生活型为'
        for attri in self.distri_attris:
            if attri == '省份':
                template_dict[attri] = '该植物广泛分布的省(市、区)有'.format(attri)
            elif attri in ('地区', '国家'):
                template_dict[attri] = '所属的{0}为'.format(attri)
        for attri in self.family_attris:
            template_dict[attri] = ''

        return template_dict

    def output(self, string):
        """输出到终端。目前是标准输出，但之后可能是对接前端"""
        print(string, end='')

    def output_node_attributes(self, attris, node_attri_dict, template_dict, isFamilyOutput=False):
        for attri in attris:
            if attri not in node_attri_dict:
                continue
            template = template_dict[attri]
            if type(node_attri_dict[attri]) == list and node_attri_dict[attri] != []:
                self.output(template)
                for idx, item in enumerate(node_attri_dict[attri]):
                    if idx != 0:
                        self.output('、')
                    self.output(item)
                self.output('。')
            elif type(node_attri_dict[attri]) == str:
                if not isFamilyOutput:
                    self.output(template)
                    self.output(node_attri_dict[attri].strip('。')+'。')
                if isFamilyOutput:
                    if attri == '界':
                        self.output('该植物属于')
                    self.output(node_attri_dict[attri])
                    self.output(template)
                    if attri == '属':
                        self.output('。')
                    else:
                        self.output('，')
        self.output('\n')

    # def cypher(self, )

    def query(self, plant_sci_name):
        """根据植物的学名，在植物知识图谱中查找，打印输出植物的各方面数据"""
        # 植物的中文名、别名、全部性状（需要做成一个自然语言表达句来返回）
        # 植物学分类，x界x门xxx属...
        # 植物的分类
        # 植物的描述
        template_dict = self.attri_chara_template()

        n_matcher = NodeMatcher(self.graph)
        node = n_matcher.match("Species", name=plant_sci_name)

        # 1.根据学名，查找结点属性
        self.output('您要查询的植物为:'+plant_sci_name+'。\n')
        node_attri_dict = dict(node.all()[0]) # type(node.all()[0]) == Node
        print(node_attri_dict, '\n^^^^^^^^^^^^')
        # TODO:考虑是否在每一个attri输出后加上换行符
        # 1.1.先输出基本信息
        self.output_node_attributes(self.node_basic_attris, node_attri_dict, template_dict)
            
        #1.2.其次，输出性状
        self.output_node_attributes(self.charas, node_attri_dict, template_dict)


        # 2.搜索所有的关系来输出结果

        # 2.1查询该物种分布的省份、地区、国家
        query_provinces = "MATCH (s:Species)-[:planted_in]->(p:{0}) WHERE s.name = '{1}' RETURN p.name".format('Province', plant_sci_name)
        query_areas = "MATCH (s:Species)-[:planted_in]->(p:{0}) WHERE s.name = '{1}' RETURN p.name".format('Area', plant_sci_name)
        query_country = "MATCH (s:Species)-[:planted_in]->(p:{0}) WHERE s.name = '{1}' RETURN p.name".format('Country', plant_sci_name)

        # 运行查询物种分布的省份、地区、国家
        results_provinces = self.graph.run(query_provinces)
        results_areas = self.graph.run(query_areas)
        results_country = self.graph.run(query_country)

        # 获得省份、地区、国家列表
        provinces = [record['p.name'] for record in results_provinces]
        areas = [record['p.name'] for record in results_areas]
        country = [record['p.name'] for record in results_country]
        
        distri_dict = {"省份": provinces, "地区": areas, "国家": country}
        self.output_node_attributes(self.distri_attris, distri_dict, template_dict)
        # 2.2查询该物种的界门纲目科属并输出字符串
        results_family = self.graph.run("MATCH (:Species {name: $name})-[:type_of]->(g:Genus)-[:subclass_of]->(f:Family)-[:subclass_of]->(o:Order)-[:subclass_of]->(c:Class)-[:subclass_of]->(p:Phylum)-[:subclass_of]->(k:Kingdom) RETURN g.name, f.name, o.name, c.name, p.name, k.name", name=plant_sci_name)
        results_family = results_family.data()[0]
        family_map = {'g.name': '属', 'f.name': '科', 'o.name': '目', 'c.name': '纲', 'p.name': '门', 'k.name': '界'}
        results_family = {family_map[key]: results_family[key] for key in family_map}
        # print(results_family)
        self.output_node_attributes(self.family_attris, results_family, template_dict, isFamilyOutput=True)

    def integrate_information(self, preliminary_results, hasGuidedUser=False):
        """
            1.接受鉴别系统给的初步鉴定结果
            2.查询若干结果的结点信息，并对比其性状，确定提问方式
            3.制作各种问题模板（独立成一个def函数）
            4.整合问题，并输出到终端，作为引导用户信息
            5.获取用户信息
            6.从用户反馈的回复
                若用户认为都不对，就不管了
                若用户选了至少一项，就选择这个结果
            7.将最终结果返回给百科系统
        """
        if not hasGuidedUser:
            # 1. preliminary_results的形式：{植物学名i：置信度i}
            
            # 2.查询结点信息，并对比其性状，确定提问方式
            # 2.1.查询结点信息
            plant_chara_dict = {}   # {plant1: {chara_name1:chara1value, chara_name2:chara2value}, plant2: {...}},是dict[dict]
            chara_plant_dict = {}   # {chara_name1: [plant1, plant2,...]},是dict[list]
            for plant_sci_name in preliminary_results:
                n_matcher = NodeMatcher(self.graph)
                node = n_matcher.match("Species", name=plant_sci_name)
                node_attri_dict = dict(node.all()[0])
                node_attri_dict.pop('描述')
                plant_chara_dict[plant_sci_name] = node_attri_dict
                for chara_name in node_attri_dict:
                    if chara_name not in chara_plant_dict:
                        chara_plant_dict[chara_name] = []
                    chara_plant_dict[chara_name].append(plant_sci_name)
            num_candidate_plants = len(plant_chara_dict)

            # 2.2.1第一种提问方式的数据准备
            common_charas = []  # 共有的性状名
            for chara_name in chara_plant_dict:
                if len(chara_plant_dict[chara_name]) == num_candidate_plants:
                    # 如果所有候选植物都具有该种性状
                    # 暂时不过滤分不开的性状
                    # if chara_name != 
                    common_charas.append(chara_name)
            # test
            print('\n\n')
            for plant in plant_chara_dict:
                for chara_name in common_charas:
                    if type(plant_chara_dict[plant][chara_name]) == list:
                        self.output(plant+"'s"+chara_name+":"+'、'.join(plant_chara_dict[plant][chara_name])+'\n')
                    else:
                        self.output(plant+"'s"+chara_name+":"+plant_chara_dict[plant][chara_name]+'\n')
                self.output('\n\n')

            # 2.2.2第二种方式的数据准备





pedia = Encyclopedia()
pedia.query('Chrysanthemum indicum')
pedia.integrate_information({'Diospyros kaki':0.9, "Diospyros lotus":0.8})