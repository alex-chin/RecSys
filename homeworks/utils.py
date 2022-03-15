import pandas as pd
import numpy as np


class PrefilterSeq:
    data = None

    def __init__(self, data, list_filter):
        self.list_filter = list_filter
        self.data = data
        self._prepare()


    def _prepare(self):
        # расчет чека
        self.data['price'] = self.data['sales_value'] / (np.maximum(self.data['quantity'], 1))

    def processing(self):
        for filter in self.list_filter:
            self.data = filter.trans(self.data)

        return self.data


class Filter:
    def __init__(self):
        pass

    def trans(self, data):
        pass


class FilterLower(Filter):
    def __init__(self, low=1):
        super().__init__()
        self.low = low

    def trans(self, data):
        return data[data['price'] > self.low]


class FilterMax(Filter):
    def __init__(self, max=60):
        super().__init__()
        self.max = max

    def trans(self, data):
        return data[data['price'] < self.max]


class FilterNonDepartment(Filter):
    def __init__(self, item_features):
        super().__init__()
        self.item_features = item_features

    def trans(self, data):
        if self.item_features is not None:
            department_size = pd.DataFrame(self.item_features. \
                                           groupby('department')['item_id'].nunique(). \
                                           sort_values(ascending=False)).reset_index()

            department_size.columns = ['department', 'n_items']
            rare_departments = department_size[department_size['n_items'] < 150].department.tolist()
            items_in_rare_departments = self.item_features[
                self.item_features['department'].isin(rare_departments)].item_id.unique().tolist()

            data = data[~data['item_id'].isin(items_in_rare_departments)]
            return data


class Popular(Filter):
    df_popularity = None

    def __init__(self):
        super().__init__()

    def trans(self, data):
        self.df_popularity = data.groupby('item_id')['user_id'].nunique().reset_index()
        self.df_popularity['share_unique_users'] = self.df_popularity['user_id'] / data['user_id'].nunique()


class OverPopular(Popular):
    def __init__(self, popularity=0.5):
        super().__init__()
        self.popularity = popularity

    def trans(self, data):
        super().trans(data)

        top_popular = self.df_popularity[self.df_popularity['share_unique_users'] > self.popularity].item_id.tolist()
        data = data[~data['item_id'].isin(top_popular)]
        return data


class LowestPopularity(Popular):
    def __init__(self, popularity=0.01):
        super().__init__()
        self.popularity = popularity

    def trans(self, data):
        super().trans(data)

        top_notpopular = self.df_popularity[self.df_popularity['share_unique_users'] < self.popularity].item_id.tolist()
        data = data[~data['item_id'].isin(top_notpopular)]
        return data


class LongTimeNoSold(Filter):
    def __init__(self, weeks=52):
        super().__init__()
        self.weeks = weeks

    def trans(self, data):
        # уберем товары, которые не продавались за последние 12 мес¤цев
        week_of_last_purchaices = data.groupby('item_id')['week_no'].max().reset_index()
        bought_year_ago = week_of_last_purchaices[
            week_of_last_purchaices['week_no'] < (data['week_no'].max() - self.weeks)].item_id.tolist()
        data = data[~data['item_id'].isin(bought_year_ago)]
        return data


class TopBayer(Filter):
    def __init__(self, take_n_popular=5000):
        super().__init__()
        self.take_n_popular = take_n_popular

    def trans(self, data):
        popularity = data.groupby('item_id')['quantity'].sum().reset_index()
        popularity.rename(columns={'quantity': 'n_sold'}, inplace=True)
        top = popularity.sort_values('n_sold', ascending=False).head(self.take_n_popular).item_id.tolist()
        data.loc[~data['item_id'].isin(top), 'item_id'] = 999999
        return data


def prefilter_items(data, take_n_popular=5000, item_features=None):
    data['price'] = data['sales_value'] / (np.maximum(data['quantity'], 1))

    # уберем слишком дешевые товары (на них не заработаем). 1 покупка из рассылок стоит 60 руб. 
    data = data[data['price'] > 1]
    # уберем слишком дорогие товары
    data = data[data['price'] < 60]

    # уберем не интересные дл¤ рекоммендаций категории (department)
    if item_features is not None:
        department_size = pd.DataFrame(item_features. \
                                       groupby('department')['item_id'].nunique(). \
                                       sort_values(ascending=False)).reset_index()

        department_size.columns = ['department', 'n_items']
        rare_departments = department_size[department_size['n_items'] < 150].department.tolist()
        items_in_rare_departments = item_features[
            item_features['department'].isin(rare_departments)].item_id.unique().tolist()

        data = data[~data['item_id'].isin(items_in_rare_departments)]

    # Уберем самые популярные товары (их и так купят)
    popularity = data.groupby('item_id')['user_id'].nunique().reset_index()
    popularity['share_unique_users'] = popularity['user_id'] / data['user_id'].nunique()

    top_popular = popularity[popularity['share_unique_users'] > 0.5].item_id.tolist()
    data = data[~data['item_id'].isin(top_popular)]

    # Уберем самые НЕ популярные товары (их и так НЕ купят)
    top_notpopular = popularity[popularity['share_unique_users'] < 0.01].item_id.tolist()
    data = data[~data['item_id'].isin(top_notpopular)]

    # уберем товары, которые не продавались за последние 12 мес¤цев
    week_of_last_purchaices = data.groupby('item_id')['week_no'].max().reset_index()
    bought_year_ago = week_of_last_purchaices[
        week_of_last_purchaices['week_no'] < (data['week_no'].max() - 52)].item_id.tolist()
    data = data[~data['item_id'].isin(bought_year_ago)]

    # Заведем фиктивный item_id (если юзер покупал товары из топ-5000, то он "купил" такой товар)
    popularity = data.groupby('item_id')['quantity'].sum().reset_index()
    popularity.rename(columns={'quantity': 'n_sold'}, inplace=True)
    top = popularity.sort_values('n_sold', ascending=False).head(take_n_popular).item_id.tolist()
    data.loc[~data['item_id'].isin(top), 'item_id'] = 999999

    return data


def postfilter_items(user_id, recommednations):
    pass
