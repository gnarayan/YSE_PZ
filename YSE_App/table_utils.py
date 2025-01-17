from django.shortcuts import render
from .models import *
from . import view_utils
import django_tables2 as tables
from django_tables2 import RequestConfig
from django.db.models import F, Q
from django.db.models.functions import Length, Substr
from django.db.models import Count, Value, Max, Min
from django.db.models.functions import Greatest, Coalesce
from django_tables2 import A
from django.db import models
from .data import PhotometryService
import time
import django_filters
import itertools
from astropy.coordinates import get_moon, SkyCoord
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from matplotlib import rcParams
rcParams['figure.figsize'] = (7,7)

class TransientTable(tables.Table):

	name_string = tables.TemplateColumn("<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
										verbose_name='Name',orderable=True,order_by='name')
	ra_string = tables.Column(accessor='CoordString.0',
							  verbose_name='RA',orderable=True,order_by='ra')
	dec_string = tables.Column(accessor='CoordString.1',
							   verbose_name='DEC',orderable=True,order_by='dec')
	disc_date_string = tables.Column(accessor='disc_date_string',
									 verbose_name='Disc. Date',orderable=True,order_by='disc_date')
	recent_mag = tables.Column(accessor='recent_mag',
							   verbose_name='Last Mag',orderable=True)
	recent_magdate = tables.Column(accessor='recent_magdate',
							   verbose_name='Last Obs. Date',orderable=True)
	best_redshift = tables.Column(accessor='z_or_hostz',
								  verbose_name='Redshift',orderable=True,order_by='host__redshift')
	
	#mw_ebv = tables.Column(accessor='mw_ebv',
	#						   verbose_name='MW E(B-V)',orderable=True)
	mw_ebv = tables.TemplateColumn("""{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
								   verbose_name='MW E(B-V)',orderable=True,order_by='mw_ebv')

	
	status_string = tables.TemplateColumn("""<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
    												<li><a data-status_id="{{ status.id }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
										  verbose_name='Status',orderable=True,order_by='status')

	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.base_columns['best_spec_class'].verbose_name = 'Spec. Class'

	def order_best_redshift(self, queryset, is_descending):

		queryset = queryset.annotate(
			best_redshift=Coalesce('redshift', 'host__redshift'),
		).order_by(('-' if is_descending else '') + 'best_redshift')
		return (queryset, True)

	
	def order_recent_mag(self, queryset, is_descending):

		all_phot = TransientPhotometry.objects.values('transient').filter(transient__in = queryset)
		phot_ids = all_phot.values('id')
		
		phot_data_query = Q(transientphotometry__id__in=phot_ids)
		queryset = queryset.annotate(
			recent_mag=Max('transientphotometry__transientphotdata__mag',filter=phot_data_query), #,filter=phot_data_query
		).order_by(('-' if is_descending else '') + 'recent_mag')
		return (queryset, True)

	def order_recent_magdate(self, queryset, is_descending):

		all_phot = TransientPhotometry.objects.values('transient').filter(transient__in = queryset)
		phot_ids = all_phot.values('id')
		
		phot_data_query = Q(transientphotometry__id__in=phot_ids)
		queryset = queryset.annotate(
			recent_magdate=Max('transientphotometry__transientphotdata__obs_date',filter=phot_data_query), #,filter=phot_data_query
		).order_by(('-' if is_descending else '') + 'recent_magdate')
		return (queryset, True)
	
	
	class Meta:
		model = Transient
		fields = ('name_string','ra_string','dec_string','disc_date_string','recent_mag','recent_magdate','mw_ebv',
				  'obs_group','best_spec_class','best_redshift','status_string')
		
		template_name='YSE_App/django-tables2/bootstrap.html'
		attrs = {
			'th' : {
				'_ordering': {
					'orderable': 'sortable', # Instead of `orderable`
					'ascending': 'ascend',	 # Instead of `asc`
					'descending': 'descend'	 # Instead of `desc`
				}
			},
			'class': 'table table-bordered table-hover',
			'id': 'k2_transient_tbl',
			"columnDefs": [
				{"type":"title-numeric","targets":1},
				{"type":"title-numeric","targets":2},
			],
			"order": [[ 3, "desc" ]],
		}

class NewTransientTable(tables.Table):

	name_string = tables.TemplateColumn("<a href=\"{% url 'transient_detail' record.slug %}\">{{ record.name }}</a>",
										verbose_name='Name',orderable=True,order_by='name')
	ra_string = tables.Column(accessor='CoordString.0',
							  verbose_name='RA',orderable=True,order_by='ra')
	dec_string = tables.Column(accessor='CoordString.1',
							   verbose_name='DEC',orderable=True,order_by='dec')
	disc_date_string = tables.Column(accessor='disc_date_string',
									 verbose_name='Disc. Date',orderable=True,order_by='disc_date')
	recent_mag = tables.Column(accessor='recent_mag',
							   verbose_name='Last Mag',orderable=True)
	recent_magdate = tables.Column(accessor='recent_magdate',
							   verbose_name='Last Obs. Date',orderable=True)
	best_redshift = tables.Column(accessor='z_or_hostz',
								  verbose_name='Redshift',orderable=True,order_by='host__redshift')
	ps_score = tables.Column(accessor='point_source_probability',
							 verbose_name='PS Score',orderable=True)
	
	#mw_ebv = tables.Column(accessor='mw_ebv',
	#						   verbose_name='MW E(B-V)',orderable=True)
	mw_ebv = tables.TemplateColumn("""{% if record.mw_ebv %}
{% if record.mw_ebv >= 0.2 %}
&nbsp;<b class="text-red">{{ record.mw_ebv }}</b>
{% else %}
{{ record.mw_ebv }}
{% endif %}
{% else %}
-
{% endif %}""",
								   verbose_name='MW E(B-V)',orderable=True,order_by='mw_ebv')

	
	status_string = tables.TemplateColumn("""<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_transient_statuses %}
    												<li><a data-status_id="{{ status.id }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
										  verbose_name='Status',orderable=True,order_by='status')

	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.base_columns['best_spec_class'].verbose_name = 'Spec. Class'

	def order_best_redshift(self, queryset, is_descending):

		queryset = queryset.annotate(
			best_redshift=Coalesce('redshift', 'host__redshift'),
		).order_by(('-' if is_descending else '') + 'best_redshift')
		return (queryset, True)

	
	def order_recent_mag(self, queryset, is_descending):

		all_phot = TransientPhotometry.objects.values('transient').filter(transient__in = queryset)
		phot_ids = all_phot.values('id')
		
		phot_data_query = Q(transientphotometry__id__in=phot_ids)
		queryset = queryset.annotate(
			recent_mag=Max('transientphotometry__transientphotdata__mag',filter=phot_data_query), #,filter=phot_data_query
		).order_by(('-' if is_descending else '') + 'recent_mag')
		return (queryset, True)

	def order_recent_magdate(self, queryset, is_descending):

		all_phot = TransientPhotometry.objects.values('transient').filter(transient__in = queryset)
		phot_ids = all_phot.values('id')
		
		phot_data_query = Q(transientphotometry__id__in=phot_ids)
		queryset = queryset.annotate(
			recent_magdate=Max('transientphotometry__transientphotdata__obs_date',filter=phot_data_query), #,filter=phot_data_query
		).order_by(('-' if is_descending else '') + 'recent_magdate')
		return (queryset, True)
	
	
	class Meta:
		model = Transient
		fields = ('name_string','ra_string','dec_string','disc_date_string','recent_mag','recent_magdate','mw_ebv',
				  'obs_group','best_spec_class','best_redshift','ps_score','status_string')
		
		template_name='YSE_App/django-tables2/bootstrap.html'
		attrs = {
			'th' : {
				'_ordering': {
					'orderable': 'sortable', # Instead of `orderable`
					'ascending': 'ascend',	 # Instead of `asc`
					'descending': 'descend'	 # Instead of `desc`
				}
			},
			'class': 'table table-bordered table-hover',
			'id': 'k2_transient_tbl',
			"columnDefs": [
				{"type":"title-numeric","targets":1},
				{"type":"title-numeric","targets":2},
			],
			"order": [[ 3, "desc" ]],
		}

		
class FollowupTable(tables.Table):

	name_string = tables.TemplateColumn("<a href=\"{% url 'transient_detail' record.transient.slug %}\">{{ record.transient.name }}</a>",
										verbose_name='Name',orderable=True,order_by='name')
	ra_string = tables.Column(accessor='transient.CoordString.0',
							  verbose_name='RA',orderable=True,order_by='transient.ra')
	dec_string = tables.Column(accessor='transient.CoordString.1',
							   verbose_name='DEC',orderable=True,order_by='transient.dec')
	recent_mag = tables.Column(accessor='transient.recent_mag',
							   verbose_name='Recent Mag',orderable=True)


	observation_window = tables.Column(accessor='observation_window',
							  verbose_name='Observation Window',orderable=True,order_by='valid_start')
	
	action = tables.TemplateColumn("<a target=\"_blank\" href=\"{% url 'admin:YSE_App_transientfollowup_change' record.id %}\">Edit</a>",
								   verbose_name='Action',orderable=False)

	status_string = tables.TemplateColumn("""<div class="btn-group">
<button style="margin-bottom:5px;" type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_followup_statuses %}
    												<li><a data-status_id="{{ status.id }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
										  verbose_name='Followup Status',orderable=True,order_by='status')

	
	
	#disc_mag = tables.Column(accessor='disc_mag',
	#						 verbose_name='Disc. Mag',orderable=True)
	
	def __init__(self,*args, **kwargs):
		super().__init__(*args, **kwargs)

		self.base_columns['transient.status'].verbose_name = 'Transient Status'
		#self.base_columns['status'].verbose_name = 'Followup Status'

	def order_recent_mag(self, queryset, is_descending):

		all_phot = TransientPhotometry.objects.values('transient').filter(transient__transientfollowup__in = queryset)
		phot_ids = all_phot.values('id')
		
		phot_data_query = Q(transient__transientphotometry__id__in=phot_ids)
		queryset = queryset.annotate(
			recent_magdate=Max('transient__transientphotometry__transientphotdata__obs_date',filter=phot_data_query), #,filter=phot_data_query
		).order_by(('-' if is_descending else '') + 'recent_magdate')
		return (queryset, True)
		
	class Meta:
		model = TransientFollowup
		fields = ('name_string','ra_string','dec_string','recent_mag','transient.status','observation_window','action')
		template_name='YSE_App/django-tables2/bootstrap.html'
		attrs = {
			'th' : {
				'_ordering': {
					'orderable': 'sortable', # Instead of `orderable`
					'ascending': 'ascend',	 # Instead of `asc`
					'descending': 'descend'	 # Instead of `desc`
				}
			},
			"columnDefs": [
				{"type":"title-numeric","targets":1},
				{"type":"title-numeric","targets":2},
			],
			'class': 'table table-bordered table-hover',
			"order": [[ 2, "desc" ]],
		}

class ObsNightFollowupTable(tables.Table):

	name_string = tables.TemplateColumn("<a href=\"{% url 'transient_detail' record.transient.slug %}\">{{ record.transient.name }}</a>",
										verbose_name='Name',orderable=True,order_by='name')
	ra_string = tables.Column(accessor='transient.CoordString.0',
							  verbose_name='RA',orderable=True,order_by='transient.ra')
	dec_string = tables.Column(accessor='transient.CoordString.1',
							   verbose_name='DEC',orderable=True,order_by='transient.dec')
	recent_mag = tables.Column(accessor='transient.recent_mag',
							   verbose_name='Recent Mag',orderable=True)


	#observation_window = tables.Column(accessor='observation_window',
	#						  verbose_name='Observation Window',orderable=True,order_by='valid_start')

	rise_time = tables.Column(verbose_name='Rise Time (UT)',orderable=False,accessor='transient.CoordString')
	set_time = tables.Column(verbose_name='Set Time (UT)',orderable=False,accessor='transient.CoordString')
	moon_angle = tables.Column(verbose_name='Moon Angle',orderable=False,accessor='transient.CoordString')
	
	status_string = tables.TemplateColumn("""<div class="btn-group">
<button style="margin-bottom:-5px;margin-top:-10px;padding:1px 5px" type="button" class="btn btn-default dropdown-toggle btn-md" data-toggle="dropdown">
											<span id="{{ record.id }}_status_name" class="dropbtn">{{ record.status }}</span>
										</button>
										<ul class="dropdown-menu">
											{% for status in all_followup_statuses %}
    												<li><a data-status_id="{{ status.id }}" transient_id="{{ record.id }}" class="transientStatusChange" href="#">{{ status.name }}</a></li>
											{% endfor %}
										</ul>
</div>""",
										  verbose_name='Followup Status',orderable=True,order_by='status')

	
	
	#disc_mag = tables.Column(accessor='disc_mag',
	#						 verbose_name='Disc. Mag',orderable=True)
	
	def __init__(self,*args, classical_obs_date=None, **kwargs):
		super().__init__(*args, **kwargs)

		self.base_columns['transient.status'].verbose_name = 'Transient Status'
		#self.base_columns['status'].verbose_name = 'Followup Status'

		location = EarthLocation.from_geodetic(
			classical_obs_date[0].resource.telescope.longitude*u.deg,classical_obs_date[0].resource.telescope.latitude*u.deg,
			classical_obs_date[0].resource.telescope.elevation*u.m)
		self.tel = Observer(location=location, timezone="UTC")
		self.tme = Time(str(classical_obs_date[0].obs_date).split()[0])
		
	def render_rise_time(self, value):
		sc = SkyCoord('%s %s'%(value[0],value[1]),unit=(u.hourangle,u.deg))
		target_rise_time = self.tel.target_rise_time(self.tme,sc,horizon=18*u.deg,which="previous")

		if target_rise_time:
			risetime = target_rise_time.isot.split('T')[-1].split('.')[0]
		else:
			risetime = None
		
		return risetime

	def render_set_time(self, value):
		sc = SkyCoord('%s %s'%(value[0],value[1]),unit=(u.hourangle,u.deg))
		target_set_time = self.tel.target_set_time(self.tme,sc,horizon=18*u.deg,which="previous")

		if target_set_time:
			settime = target_set_time.isot.split('T')[-1].split('.')[0]
		else:
			settime = None
		
		return settime

	def render_moon_angle(self, value):
		mooncoord = get_moon(self.tme)
		sc = SkyCoord('%s %s'%(value[0],value[1]),unit=(u.hourangle,u.deg))
		return('%.1f'%sc.separation(mooncoord).deg)
	
	def render_airmass(self, value):
		from astroplan.plots import plot_airmass
	
	def order_recent_mag(self, queryset, is_descending):

		all_phot = TransientPhotometry.objects.values('transient').filter(transient__transientfollowup__in = queryset)
		phot_ids = all_phot.values('id')
		
		phot_data_query = Q(transient__transientphotometry__id__in=phot_ids)
		queryset = queryset.annotate(
			recent_magdate=Max('transient__transientphotometry__transientphotdata__obs_date',filter=phot_data_query), #,filter=phot_data_query
		).order_by(('-' if is_descending else '') + 'recent_magdate')
		return (queryset, True)
		
	class Meta:
		model = TransientFollowup
		fields = ('name_string','ra_string','dec_string','recent_mag','rise_time','set_time','moon_angle','transient.status')
		template_name='YSE_App/django-tables2/bootstrap.html'
		attrs = {
			'th' : {
				'_ordering': {
					'orderable': 'sortable', # Instead of `orderable`
					'ascending': 'ascend',	 # Instead of `asc`
					'descending': 'descend'	 # Instead of `desc`
				}
			},
			"columnDefs": [
				{"type":"title-numeric","targets":1},
				{"type":"title-numeric","targets":2},
			],
			'class': 'table table-bordered table-hover',
			"order": [[ 2, "desc" ]],
		}

		
def annotate_with_disc_mag(qs):

	all_phot = TransientPhotometry.objects.values('transient')#.filter(transient__in = queryset)
	phot_ids = all_phot.values('id')
	
	phot_data_query = Q(transientphotometry__id__in=phot_ids)
	disc_query = Q(transientphotometry__transientphotdata__discovery_point = 1)
	
	qs = qs.annotate(
		disc_mag=Min('transientphotometry__transientphotdata__mag',filter=phot_data_query & disc_query),
	)
	
	qs = qs.annotate(
		obs_group_name=Min('obs_group__name'),
		host_redshift=Min('host__redshift'),
		spec_class=Min('best_spec_class__name'),
		status_name=Min('status__name'))
	return qs
	
class TransientFilter(django_filters.FilterSet):

	#name_string = django_filters.CharFilter(name='name',lookup_expr='icontains',
	#										label='Name')
	
	ex = django_filters.CharFilter(method='filter_ex',label='Search')
	search_fields = ['name','ra','dec','disc_date','disc_mag','obs_group_name',
					 'spec_class','redshift','host_redshift',
					 'status_name']

	class Meta:
		model = Transient
		fields = ['ex',]
	
	def filter_ex(self, qs, name, value):
		if value:
			
			qs = annotate_with_disc_mag(qs)

			q_parts = value.split()


			list1=self.search_fields
			list2=q_parts
			perms = [zip(x,list2) for x in itertools.permutations(list1,len(list2))]

			q_totals = Q()
			for perm in perms:
				q_part = Q()
				for p in perm:
					q_part = q_part & Q(**{p[0]+'__icontains': p[1]})
				q_totals = q_totals | q_part

			qs = qs.filter(q_totals)
		return qs

class FollowupFilter(django_filters.FilterSet):
	
	ex = django_filters.CharFilter(method='filter_ex',label='Search')
	search_fields = ['transient__name','transient__status__name','status__name','valid_start','valid_stop']

	class Meta:
		model = TransientFollowup
		fields = ['ex',]
	
	def filter_ex(self, qs, name, value):
		if value:
			q_parts = value.split()

			list1=self.search_fields
			list2=q_parts
			perms = [zip(x,list2) for x in itertools.permutations(list1,len(list2))]

			q_totals = Q()
			for perm in perms:
				q_part = Q()
				for p in perm:
					q_part = q_part & Q(**{p[0]+'__icontains': p[1]})
				q_totals = q_totals | q_part

			qs = qs.filter(q_totals)
		return qs

class ObsNightFollowupFilter(django_filters.FilterSet):
	
	ex = django_filters.CharFilter(method='filter_ex',label='Search')
	search_fields = ['transient__name','transient__status__name','status__name','valid_start','valid_stop']

	class Meta:
		model = TransientFollowup
		fields = ['ex',]
	
	def filter_ex(self, qs, name, value):
		if value:
			q_parts = value.split()

			list1=self.search_fields
			list2=q_parts
			perms = [zip(x,list2) for x in itertools.permutations(list1,len(list2))]

			q_totals = Q()
			for perm in perms:
				q_part = Q()
				for p in perm:
					q_part = q_part & Q(**{p[0]+'__icontains': p[1]})
				q_totals = q_totals | q_part

			qs = qs.filter(q_totals)
		return qs

	
	
def dashboard_tables(request):
	
	k2_transients = Transient.objects.all()
	
	table = TransientTable(k2_transients)
	RequestConfig(request, paginate={'per_page': 10}).configure(table)
			
	context = {'k2_transients': table}
	
	return render(request, 'YSE_App/dashboard_table.html', context)
