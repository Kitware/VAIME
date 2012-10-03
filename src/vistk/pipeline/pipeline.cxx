/*ckwg +5
 * Copyright 2011-2012 by Kitware, Inc. All Rights Reserved. Please refer to
 * KITWARE_LICENSE.TXT for licensing information, or contact General Counsel,
 * Kitware, Inc., 28 Corporate Drive, Clifton Park, NY 12065.
 */

#include "pipeline.h"
#include "pipeline_exception.h"

#include "edge.h"
#include "process_exception.h"
#include "process_cluster.h"

#include <boost/algorithm/string/predicate.hpp>
#include <boost/graph/directed_graph.hpp>
#include <boost/graph/topological_sort.hpp>
#include <boost/math/common_factor_rt.hpp>
#include <boost/bind.hpp>
#include <boost/foreach.hpp>
#include <boost/function.hpp>
#include <boost/functional.hpp>
#include <boost/make_shared.hpp>

#include <functional>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <stack>
#include <string>
#include <vector>

#include <cstddef>

/**
 * \file pipeline.cxx
 *
 * \brief Implementation of the base class for \link vistk::pipeline pipelines\endlink.
 */

namespace vistk
{

class pipeline::priv
{
  public:
    priv(pipeline* pipe, config_t conf);
    ~priv();

    void check_duplicate_name(process::name_t const& name);
    void remove_from_pipeline(process::name_t const& name);
    void propagate(process::name_t const& root);

    typedef std::map<process::name_t, process_t> process_map_t;
    typedef std::stack<process::name_t> parent_stack_t;
    typedef std::map<process::name_t, process::name_t> process_parent_map_t;
    typedef std::map<process::name_t, process_cluster_t> cluster_map_t;
    typedef std::map<size_t, edge_t> edge_map_t;

    typedef enum
    {
      cluster_upstream,
      cluster_downstream
    } cluster_connection_type_t;
    typedef std::pair<process::connection_t, cluster_connection_type_t> cluster_connection_t;
    typedef std::vector<cluster_connection_t> cluster_connections_t;

    typedef enum
    {
      push_upstream,
      push_downstream
    } direction_t;
    typedef std::pair<process::connection_t, direction_t> type_pinning_t;
    typedef std::vector<type_pinning_t> type_pinnings_t;

    typedef enum
    {
      type_deferred,
      type_mismatch,
      type_compatible
    } port_type_status;

    // Steps for checking a connection.
    port_type_status check_connection_types(process::connection_t const& connection, process::port_type_t const& up_type, process::port_type_t const& down_type);
    bool check_connection_flags(process::port_flags_t const& up_flags, process::port_flags_t const& down_flags) const;

    // Steps for setting up the pipeline.
    void check_for_processes() const;
    void map_cluster_connections();
    void configure_processes();
    void check_for_data_dep_ports() const;
    void propagate_pinned_types();
    void check_for_untyped_ports() const;
    void make_connections();
    void check_for_required_ports() const;
    void check_for_dag() const;
    void initialize_processes();
    void check_port_frequencies() const;

    void ensure_setup() const;

    pipeline* const q;
    config_t const config;

    process::connections_t planned_connections;
    process::connections_t connections;

    process_map_t process_map;
    cluster_map_t cluster_map;
    edge_map_t edge_map;

    process_parent_map_t process_parent_map;
    parent_stack_t parent_stack;

    process::connections_t data_dep_connections;
    cluster_connections_t cluster_connections;
    process::connections_t untyped_connections;
    type_pinnings_t type_pinnings;

    bool setup;
    bool setup_in_progress;
    bool setup_successful;
    bool running;

    static bool is_upstream_for(process::port_addr_t const& addr, process::connection_t const& connection);
    static bool is_downstream_for(process::port_addr_t const& addr, process::connection_t const& connection);
    static bool is_cluster_upstream_for(process::port_addr_t const& addr, cluster_connection_t const& cconnection);
    static bool is_cluster_downstream_for(process::port_addr_t const& addr, cluster_connection_t const& cconnection);
    static bool is_addr_on(process::name_t const& name, process::port_addr_t const& addr);
    static bool is_connection_with(process::name_t const& name, process::connection_t const& connection);
    static bool is_cluster_connection_with(process::name_t const& name, cluster_connection_t const& cconnection);
    static bool is_cluster_connection_for(process::connection_t const& connection, cluster_connection_t const& cconnection);

    static process::port_t const port_sep;
    static config::key_t const config_edge;
    static config::key_t const config_edge_type;
    static config::key_t const config_edge_conn;

    class propagation_exception
      : public pipeline_exception
    {
      public:
        propagation_exception(process::name_t const& upstream_name,
                              process::port_t const& upstream_port,
                              process::name_t const& downstream_name,
                              process::port_t const& downstream_port,
                              process::port_type_t const& type,
                              bool push_upstream) throw();
        ~propagation_exception() throw();

        process::name_t const m_upstream_name;
        process::port_t const m_upstream_port;
        process::name_t const m_downstream_name;
        process::port_t const m_downstream_port;
        process::port_type_t const m_type;
        bool const m_push_upstream;
    };
};

process::port_t const pipeline::priv::port_sep = config::key_t(".");
config::key_t const pipeline::priv::config_edge = config::key_t("_edge");
config::key_t const pipeline::priv::config_edge_type = config::key_t("_edge_by_type");
config::key_t const pipeline::priv::config_edge_conn = config::key_t("_edge_by_conn");

pipeline
::pipeline(config_t const& config)
  : d()
{
  d.reset(new priv(this, config));

  if (!config)
  {
    throw null_pipeline_config_exception();
  }
}

pipeline
::~pipeline()
{
}

void
pipeline
::add_process(process_t const& process)
{
  if (!process)
  {
    throw null_process_addition_exception();
  }

  if (d->setup)
  {
    throw add_after_setup_exception(process->name());
  }

  process::name_t const name = process->name();

  d->check_duplicate_name(name);

  process_cluster_t const cluster = boost::dynamic_pointer_cast<process_cluster>(process);

  process::name_t parent;

  if (!d->parent_stack.empty())
  {
    parent = d->parent_stack.top();
  }

  if (cluster)
  {
    d->cluster_map[name] = cluster;
    d->process_parent_map[name] = parent;

    d->parent_stack.push(name);

    /// \todo Should failure to add a cluster be able to be rolled back?

    processes_t const cluster_procs = cluster->processes();

    BOOST_FOREACH (process_t const& cluster_proc, cluster_procs)
    {
      add_process(cluster_proc);
    }

    process::connections_t const& connections = cluster->internal_connections();

    BOOST_FOREACH (process::connection_t const& connection, connections)
    {
      process::port_addr_t const& upstream_addr = connection.first;
      process::port_addr_t const& downstream_addr = connection.second;

      process::name_t const& upstream_name = upstream_addr.first;
      process::port_t const& upstream_port = upstream_addr.second;
      process::name_t const& downstream_name = downstream_addr.first;
      process::port_t const& downstream_port = downstream_addr.second;

      connect(upstream_name, upstream_port,
              downstream_name, downstream_port);
    }

    d->parent_stack.pop();

    return;
  }

  d->process_map[name] = process;
  d->process_parent_map[name] = parent;
}

void
pipeline
::remove_process(process::name_t const& name)
{
  if (d->setup)
  {
    throw remove_after_setup_exception(name);
  }

  priv::cluster_map_t::iterator const i = d->cluster_map.find(name);

  if (i != d->cluster_map.end())
  {
    process_cluster_t const& cluster = i->second;

    processes_t const cluster_procs = cluster->processes();

    BOOST_FOREACH (process_t const& cluster_proc, cluster_procs)
    {
      process::name_t const& cluster_proc_name = cluster_proc->name();

      remove_process(cluster_proc_name);
    }

    d->cluster_map.erase(i);

    return;
  }

  /// \todo If process is in a cluster, remove the cluster.

  priv::process_map_t::const_iterator const j = d->process_map.find(name);

  if (j == d->process_map.end())
  {
    throw no_such_process_exception(name);
  }

  d->process_map.erase(name);

  d->remove_from_pipeline(name);
}

void
pipeline
::connect(process::name_t const& upstream_name,
          process::port_t const& upstream_port,
          process::name_t const& downstream_name,
          process::port_t const& downstream_port)
{
  if (d->setup && !d->setup_in_progress)
  {
    throw connection_after_setup_exception(upstream_name, upstream_port,
                                           downstream_name, downstream_port);
  }

  process::port_addr_t const up_addr = process::port_addr_t(upstream_name, upstream_port);
  process::port_addr_t const down_addr = process::port_addr_t(downstream_name, downstream_port);
  process::connection_t const connection = process::connection_t(up_addr, down_addr);

  if (!d->setup_in_progress)
  {
    d->planned_connections.push_back(connection);
  }

  priv::cluster_map_t::const_iterator const up_cluster_it = d->cluster_map.find(upstream_name);
  priv::cluster_map_t::const_iterator const down_cluster_it = d->cluster_map.find(downstream_name);

  bool const upstream_is_cluster = (up_cluster_it != d->cluster_map.end());
  bool const downstream_is_cluster = (down_cluster_it != d->cluster_map.end());

  if (upstream_is_cluster || downstream_is_cluster)
  {
    if (upstream_is_cluster)
    {
      d->cluster_connections.push_back(priv::cluster_connection_t(connection, priv::cluster_upstream));
    }
    else if (downstream_is_cluster)
    {
      d->cluster_connections.push_back(priv::cluster_connection_t(connection, priv::cluster_downstream));
    }

    return;
  }

  process_t const up_proc = process_by_name(upstream_name);
  process_t const down_proc = process_by_name(downstream_name);

  process::port_info_t const up_info = up_proc->output_port_info(upstream_port);
  process::port_info_t const down_info = down_proc->input_port_info(downstream_port);

  process::port_flags_t const& up_flags = up_info->flags;
  process::port_flags_t const& down_flags = down_info->flags;

  if (!d->check_connection_flags(up_flags, down_flags))
  {
    throw connection_flag_mismatch_exception(upstream_name, upstream_port,
                                             downstream_name, downstream_port);
  }

  process::port_type_t const& up_type = up_info->type;
  process::port_type_t const& down_type = down_info->type;

  switch (d->check_connection_types(connection, up_type, down_type))
  {
    case priv::type_deferred:
      return;
    case priv::type_mismatch:
      throw connection_type_mismatch_exception(upstream_name, upstream_port, up_type,
                                               downstream_name, downstream_port, down_type);
    case priv::type_compatible:
    default:
      break;
  }

  d->connections.push_back(connection);
}

void
pipeline
::disconnect(process::name_t const& upstream_name,
             process::port_t const& upstream_port,
             process::name_t const& downstream_name,
             process::port_t const& downstream_port)
{
  if (d->setup)
  {
    throw disconnection_after_setup_exception(upstream_name, upstream_port,
                                              downstream_name, downstream_port);
  }

  process::port_addr_t const upstream_addr = process::port_addr_t(upstream_name, upstream_port);
  process::port_addr_t const downstream_addr = process::port_addr_t(downstream_name, downstream_port);
  process::connection_t const conn = process::connection_t(upstream_addr, downstream_addr);

  boost::function<bool (process::connection_t const&)> const eq = boost::bind(std::equal_to<process::connection_t>(), conn, _1);
  boost::function<bool (priv::cluster_connection_t const&)> const cluster_eq = boost::bind(&priv::is_cluster_connection_for, conn, _1);

#define FORGET_CONNECTION(T, f, conns)                                   \
  do                                                                     \
  {                                                                      \
    T::iterator const i = std::remove_if(conns.begin(), conns.end(), f); \
    conns.erase(i, conns.end());                                         \
  } while (false)

  FORGET_CONNECTION(process::connections_t, eq, d->planned_connections);
  FORGET_CONNECTION(process::connections_t, eq, d->connections);
  FORGET_CONNECTION(process::connections_t, eq, d->data_dep_connections);
  FORGET_CONNECTION(process::connections_t, eq, d->untyped_connections);
  FORGET_CONNECTION(priv::cluster_connections_t, cluster_eq, d->cluster_connections);

#undef FORGET_CONNECTION
}

void
pipeline
::setup_pipeline()
{
  if (d->setup)
  {
    throw pipeline_duplicate_setup_exception();
  }

  d->check_for_processes();

  // There's no turning back after this (processes are modified and may not be
  // able to be added/removed without compromising the checks after this point).
  d->setup = true;
  d->setup_in_progress = true;
  d->setup_successful = false;

  try
  {
    d->map_cluster_connections();
    d->configure_processes();
    d->check_for_data_dep_ports();
    d->propagate_pinned_types();
    d->check_for_untyped_ports();
    d->make_connections();
    d->check_for_required_ports();
    d->check_for_dag();
    d->initialize_processes();
    d->check_port_frequencies();
  }
  catch (...)
  {
    d->setup_in_progress = false;
    throw;
  }

  d->setup_in_progress = false;
  d->setup_successful = true;
}

bool
pipeline
::is_setup() const
{
  return d->setup;
}

bool
pipeline
::setup_successful() const
{
  return d->setup_successful;
}

void
pipeline
::reset()
{
  if (d->running)
  {
    throw reset_running_pipeline_exception();
  }

  d->setup = false;
  d->setup_successful = false;

  priv::process_map_t const names = d->process_map;

  // Reset all the processes.
  BOOST_FOREACH (priv::process_map_t::value_type& process_entry, d->process_map)
  {
    process_t const& process = process_entry.second;

    process->reset();
  }

  // Clear internal bookkeeping.
  d->connections.clear();
  d->edge_map.clear();
  d->data_dep_connections.clear();
  d->cluster_connections.clear();
  d->untyped_connections.clear();
  d->type_pinnings.clear();

  d->setup_in_progress = true;

  // Replay connections.
  BOOST_FOREACH (process::connection_t const& connection, d->planned_connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;
    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    connect(upstream_name, upstream_port,
            downstream_name, downstream_port);
  }

  d->setup_in_progress = false;
}

process::names_t
pipeline
::process_names() const
{
  process::names_t names;

  BOOST_FOREACH (priv::process_map_t::value_type const& process_index, d->process_map)
  {
    process::name_t const& name = process_index.first;

    names.push_back(name);
  }

  return names;
}

process_t
pipeline
::process_by_name(process::name_t const& name) const
{
  priv::process_map_t::const_iterator i = d->process_map.find(name);

  if (i == d->process_map.end())
  {
    throw no_such_process_exception(name);
  }

  return i->second;
}

process::name_t
pipeline
::parent_cluster(process::name_t const& name) const
{
  priv::process_parent_map_t::const_iterator i = d->process_parent_map.find(name);

  if (i == d->process_parent_map.end())
  {
    throw no_such_process_exception(name);
  }

  return i->second;
}

process::names_t
pipeline
::cluster_names() const
{
  process::names_t names;

  BOOST_FOREACH (priv::cluster_map_t::value_type const& cluster, d->cluster_map)
  {
    process::name_t const& name = cluster.first;

    names.push_back(name);
  }

  return names;
}

process_cluster_t
pipeline
::cluster_by_name(process::name_t const& name) const
{
  priv::cluster_map_t::const_iterator i = d->cluster_map.find(name);

  if (i == d->cluster_map.end())
  {
    throw no_such_process_exception(name);
  }

  return i->second;
}

process::port_addrs_t
pipeline
::connections_from_addr(process::name_t const& name, process::port_t const& port) const
{
  process::port_addrs_t addrs;

  BOOST_FOREACH (process::connection_t const& connection, d->planned_connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;

    if ((upstream_name == name) && (upstream_port == port))
    {
      addrs.push_back(downstream_addr);
    }
  }

  return addrs;
}

process::port_addr_t
pipeline
::connection_to_addr(process::name_t const& name, process::port_t const& port) const
{
  BOOST_FOREACH (process::connection_t const& connection, d->planned_connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    if ((downstream_name == name) && (downstream_port == port))
    {
      return upstream_addr;
    }
  }

  return process::port_addr_t();
}

processes_t
pipeline
::upstream_for_process(process::name_t const& name) const
{
  d->ensure_setup();

  std::set<process::name_t> names;

  BOOST_FOREACH (process::connection_t const& connection, d->connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::name_t const& downstream_name = downstream_addr.first;

    if (downstream_name == name)
    {
      names.insert(upstream_name);
    }
  }

  processes_t processes;

  BOOST_FOREACH (process::name_t const& process_name, names)
  {
    priv::process_map_t::const_iterator i = d->process_map.find(process_name);
    process_t const& process = i->second;

    processes.push_back(process);
  }

  return processes;
}

process_t
pipeline
::upstream_for_port(process::name_t const& name, process::port_t const& port) const
{
  d->ensure_setup();

  BOOST_FOREACH (process::connection_t const& connection, d->connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    if ((downstream_name == name) &&
        (downstream_port == port))
    {
      priv::process_map_t::const_iterator const i = d->process_map.find(upstream_name);

      return i->second;
    }
  }

  return process_t();
}

processes_t
pipeline
::downstream_for_process(process::name_t const& name) const
{
  d->ensure_setup();

  std::set<process::name_t> names;

  BOOST_FOREACH (process::connection_t const& connection, d->connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::name_t const& downstream_name = downstream_addr.first;

    if (upstream_name == name)
    {
      names.insert(downstream_name);
    }
  }

  processes_t processes;

  BOOST_FOREACH (process::name_t const& process_name, names)
  {
    priv::process_map_t::const_iterator const i = d->process_map.find(process_name);
    process_t const& process = i->second;

    processes.push_back(process);
  }

  return processes;
}

processes_t
pipeline
::downstream_for_port(process::name_t const& name, process::port_t const& port) const
{
  d->ensure_setup();

  std::set<process::name_t> names;

  BOOST_FOREACH (process::connection_t const& connection, d->connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;
    process::name_t const& downstream_name = downstream_addr.first;

    if ((upstream_name == name) &&
        (upstream_port == port))
    {
      names.insert(downstream_name);
    }
  }

  processes_t processes;

  BOOST_FOREACH (process::name_t const& process_name, names)
  {
    priv::process_map_t::const_iterator const i = d->process_map.find(process_name);
    process_t const& process = i->second;

    processes.push_back(process);
  }

  return processes;
}

process::port_addr_t
pipeline
::sender_for_port(process::name_t const& name, process::port_t const& port) const
{
  d->ensure_setup();

  BOOST_FOREACH (process::connection_t const& connection, d->connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    if ((downstream_name == name) &&
        (downstream_port == port))
    {
      return upstream_addr;
    }
  }

  return process::port_addr_t();
}

process::port_addrs_t
pipeline
::receivers_for_port(process::name_t const& name, process::port_t const& port) const
{
  d->ensure_setup();

  process::port_addrs_t port_addrs;

  BOOST_FOREACH (process::connection_t const& connection, d->connections)
  {
    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;

    if ((upstream_name == name) &&
        (upstream_port == port))
    {
      port_addrs.push_back(downstream_addr);
    }
  }

  return port_addrs;
}

edge_t
pipeline
::edge_for_connection(process::name_t const& upstream_name,
                      process::port_t const& upstream_port,
                      process::name_t const& downstream_name,
                      process::port_t const& downstream_port) const
{
  d->ensure_setup();

  for (size_t i = 0; i < d->connections.size(); ++i)
  {
    process::connection_t const& connection = d->connections[i];

    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& up_name = upstream_addr.first;
    process::port_t const& up_port = upstream_addr.second;
    process::name_t const& down_name = downstream_addr.first;
    process::port_t const& down_port = downstream_addr.second;

    if ((up_name == upstream_name) &&
        (up_port == upstream_port) &&
        (down_name == downstream_name) &&
        (down_port == downstream_port))
    {
      return d->edge_map[i];
    }
  }

  return edge_t();
}

edges_t
pipeline
::input_edges_for_process(process::name_t const& name) const
{
  d->ensure_setup();

  edges_t edges;

  BOOST_FOREACH (priv::edge_map_t::value_type const& edge_index, d->edge_map)
  {
    size_t const& i = edge_index.first;
    edge_t const& edge = edge_index.second;

    process::connection_t const connection = d->connections[i];

    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& downstream_name = downstream_addr.first;

    if (downstream_name == name)
    {
      edges.push_back(edge);
    }
  }

  return edges;
}

edge_t
pipeline
::input_edge_for_port(process::name_t const& name, process::port_t const& port) const
{
  d->ensure_setup();

  BOOST_FOREACH (priv::edge_map_t::value_type const& edge_index, d->edge_map)
  {
    size_t const& i = edge_index.first;
    edge_t const& edge = edge_index.second;

    process::connection_t const connection = d->connections[i];

    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    if ((downstream_name == name) &&
        (downstream_port == port))
    {
      return edge;
    }
  }

  return edge_t();
}

edges_t
pipeline
::output_edges_for_process(process::name_t const& name) const
{
  d->ensure_setup();

  edges_t edges;

  BOOST_FOREACH (priv::edge_map_t::value_type const& edge_index, d->edge_map)
  {
    size_t const& i = edge_index.first;
    edge_t const& edge = edge_index.second;

    process::connection_t const connection = d->connections[i];

    process::port_addr_t const& upstream_addr = connection.first;

    process::name_t const& upstream_name = upstream_addr.first;

    if (upstream_name == name)
    {
      edges.push_back(edge);
    }
  }

  return edges;
}

edges_t
pipeline
::output_edges_for_port(process::name_t const& name, process::port_t const& port) const
{
  d->ensure_setup();

  edges_t edges;

  BOOST_FOREACH (priv::edge_map_t::value_type const& edge_index, d->edge_map)
  {
    size_t const& i = edge_index.first;
    edge_t const& edge = edge_index.second;

    process::connection_t const connection = d->connections[i];

    process::port_addr_t const& upstream_addr = connection.first;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;

    if ((upstream_name == name) &&
        (upstream_port == port))
    {
      edges.push_back(edge);
    }
  }

  return edges;
}

void
pipeline
::start()
{
  d->ensure_setup();

  d->running = true;
}

void
pipeline
::stop()
{
  if (!d->running)
  {
    static std::string const reason = "Start/stop pipeline state tracking failed";

    throw std::logic_error(reason);
  }

  d->running = false;
}

pipeline::priv
::priv(pipeline* pipe, config_t conf)
  : q(pipe)
  , config(conf)
  , planned_connections()
  , connections()
  , process_map()
  , cluster_map()
  , edge_map()
  , data_dep_connections()
  , untyped_connections()
  , type_pinnings()
  , setup(false)
  , setup_in_progress(false)
  , setup_successful(false)
  , running(false)
{
}

pipeline::priv
::~priv()
{
}

void
pipeline::priv
::check_duplicate_name(process::name_t const& name)
{
  process_map_t::const_iterator const proc_it = process_map.find(name);
  cluster_map_t::const_iterator const cluster_it = cluster_map.find(name);

  if ((proc_it != process_map.end()) ||
      (cluster_it != cluster_map.end()))
  {
    throw duplicate_process_name_exception(name);
  }
}

void
pipeline::priv
::remove_from_pipeline(process::name_t const& name)
{
  boost::function<bool (process::connection_t const&)> const is = boost::bind(&is_connection_with, name, _1);
  boost::function<bool (cluster_connection_t const&)> const cluster_is = boost::bind(&is_cluster_connection_with, name, _1);

#define FORGET_CONNECTIONS(T, f, conns)                                  \
  do                                                                     \
  {                                                                      \
    T::iterator const i = std::remove_if(conns.begin(), conns.end(), f); \
    conns.erase(i, conns.end());                                         \
  } while (false)

  FORGET_CONNECTIONS(process::connections_t, is, planned_connections);
  FORGET_CONNECTIONS(process::connections_t, is, connections);
  FORGET_CONNECTIONS(process::connections_t, is, data_dep_connections);
  FORGET_CONNECTIONS(process::connections_t, is, untyped_connections);
  FORGET_CONNECTIONS(cluster_connections_t, cluster_is, cluster_connections);

#undef FORGET_CONNECTIONS
}

pipeline::priv::port_type_status
pipeline::priv
::check_connection_types(process::connection_t const& connection, process::port_type_t const& up_type, process::port_type_t const& down_type)
{
  bool const up_data_dep = (up_type == process::type_data_dependent);

  if (up_data_dep)
  {
    data_dep_connections.push_back(connection);

    return type_deferred;
  }

  bool const up_flow_dep = boost::starts_with(up_type, process::type_flow_dependent);
  bool const down_flow_dep = boost::starts_with(down_type, process::type_flow_dependent);

  if (up_flow_dep || down_flow_dep)
  {
    if (up_flow_dep && down_flow_dep)
    {
      untyped_connections.push_back(connection);
    }
    else if (up_flow_dep)
    {
      type_pinnings.push_back(priv::type_pinning_t(connection, priv::push_upstream));
    }
    else if (down_flow_dep)
    {
      type_pinnings.push_back(priv::type_pinning_t(connection, priv::push_downstream));
    }

    return type_deferred;
  }
  else if ((up_type != process::type_any) &&
           (down_type != process::type_any) &&
           (up_type != down_type))
  {
    return type_mismatch;
  }

  return type_compatible;
}

bool
pipeline::priv
::check_connection_flags(process::port_flags_t const& up_flags, process::port_flags_t const& down_flags) const
{
  process::port_flags_t::const_iterator i;

  i = up_flags.find(process::flag_output_const);

  bool const is_const = (i != up_flags.end());

  i = down_flags.find(process::flag_input_mutable);

  bool const requires_mutable = (i != down_flags.end());

  if (is_const && requires_mutable)
  {
    return false;
  }

  return true;
}

void
pipeline::priv
::propagate(process::name_t const& root)
{
  std::queue<process::name_t> kyu;

  kyu.push(root);

  while (!kyu.empty())
  {
    process::name_t const name = kyu.front();
    kyu.pop();

    process_t const proc = q->process_by_name(name);

    process::connections_t const conns = untyped_connections;
    untyped_connections.clear();

    BOOST_FOREACH (process::connection_t const& connection, conns)
    {
      process::port_addr_t const& upstream_addr = connection.first;
      process::port_addr_t const& downstream_addr = connection.second;
      process::name_t const& upstream_name = upstream_addr.first;
      process::port_t const& upstream_port = upstream_addr.second;
      process::name_t const& downstream_name = downstream_addr.first;
      process::port_t const& downstream_port = downstream_addr.second;

      bool resolved = false;

      if (downstream_name == name)
      {
        // Push up.
        process::port_info_t const info = proc->input_port_info(downstream_port);
        process::port_type_t const& type = info->type;

        bool const flow_dep = boost::starts_with(type, process::type_flow_dependent);

        if (!flow_dep)
        {
          process_t const up_proc = q->process_by_name(upstream_name);

          if (!up_proc->set_output_port_type(upstream_port, type))
          {
            throw propagation_exception(upstream_name, upstream_port,
                                        downstream_name, downstream_port,
                                        type, true);
          }

          resolved = true;

          q->connect(upstream_name, upstream_port,
                     downstream_name, downstream_port);

          kyu.push(upstream_name);
        }
      }
      else if (upstream_name == name)
      {
        // Push down.
        process::port_info_t const info = proc->output_port_info(upstream_port);
        process::port_type_t const& type = info->type;

        bool const flow_dep = boost::starts_with(type, process::type_flow_dependent);

        if (!flow_dep)
        {
          process_t const down_proc = q->process_by_name(downstream_name);

          if (!down_proc->set_input_port_type(downstream_port, type))
          {
            throw propagation_exception(upstream_name, upstream_port,
                                        downstream_name, downstream_port,
                                        type, false);
          }

          resolved = true;

          q->connect(upstream_name, upstream_port,
                     downstream_name, downstream_port);

          kyu.push(downstream_name);
        }
      }

      if (!resolved)
      {
        // Remember that the resolution didn't happen.
        untyped_connections.push_back(connection);
      }
    }
  }
}

void
pipeline::priv
::check_for_processes() const
{
  if (!process_map.size())
  {
    throw no_processes_exception();
  }
}

void
pipeline::priv
::map_cluster_connections()
{
  cluster_connections_t const cconnections = cluster_connections;

  // Forget the connections we'll be mapping.
  cluster_connections.clear();

  BOOST_FOREACH (cluster_connection_t const& cconnection, cconnections)
  {
    process::connection_t const& connection = cconnection.first;
    cluster_connection_type_t const& type = cconnection.second;

    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;
    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    switch (type)
    {
      case cluster_upstream:
        {
          process::name_t const& cluster_name = upstream_name;
          process::port_t const& cluster_port = upstream_port;

          cluster_map_t::const_iterator const cluster_it = cluster_map.find(cluster_name);

          if (cluster_it == cluster_map.end())
          {
            throw no_such_process_exception(cluster_name);
          }

          process_cluster_t const& cluster = cluster_it->second;
          process::connections_t mapped_connections = cluster->output_mappings();

          boost::function<bool (process::connection_t const&)> const is_port = boost::bind(&is_downstream_for, upstream_addr, _1);

          process::connections_t::iterator const i = std::remove_if(mapped_connections.begin(), mapped_connections.end(), boost::not1(is_port));
          mapped_connections.erase(i, mapped_connections.end());

          if (mapped_connections.empty())
          {
            throw no_such_port_exception(cluster_name, cluster_port);
          }
          else if (mapped_connections.size() != 1)
          {
            static std::string const reason = "Failed to ensure that only one output "
                                              "mapping is allowed on a cluster port";

            throw std::logic_error(reason);
          }

          process::connection_t const& mapped_port_conn = mapped_connections[0];
          process::port_addr_t const& mapped_port_addr = mapped_port_conn.first;

          process::name_t const& mapped_name = mapped_port_addr.first;
          process::port_t const& mapped_port = mapped_port_addr.second;

          q->connect(mapped_name, mapped_port,
                     downstream_name, downstream_port);
        }

        break;
      case cluster_downstream:
        {
          process::name_t const& cluster_name = downstream_name;
          process::port_t const& cluster_port = downstream_port;

          cluster_map_t::const_iterator const cluster_it = cluster_map.find(cluster_name);

          if (cluster_it == cluster_map.end())
          {
            throw no_such_process_exception(cluster_name);
          }

          process_cluster_t const& cluster = cluster_it->second;
          process::connections_t mapped_connections = cluster->input_mappings();

          boost::function<bool (process::connection_t const&)> const is_port = boost::bind(&is_upstream_for, downstream_addr, _1);

          process::connections_t::iterator const i = std::remove_if(mapped_connections.begin(), mapped_connections.end(), boost::not1(is_port));
          mapped_connections.erase(i, mapped_connections.end());

          if (mapped_connections.empty())
          {
            throw no_such_port_exception(cluster_name, cluster_port);
          }

          BOOST_FOREACH (process::connection_t const& mapped_port_conn, mapped_connections)
          {
            process::port_addr_t const& mapped_port_addr = mapped_port_conn.second;

            process::name_t const& mapped_name = mapped_port_addr.first;
            process::port_t const& mapped_port = mapped_port_addr.second;

            q->connect(upstream_name, upstream_port,
                       mapped_name, mapped_port);
          }
        }

        break;
      default:
        break;
    }
  }

  // Cluster ports could be mapped to other cluster ports. We need to call again
  // until every cluster port has been resolved to a process.
  if (!cluster_connections.empty())
  {
    map_cluster_connections();
  }
}

void
pipeline::priv
::configure_processes()
{
  process::names_t const names = q->process_names();

  // Configure processes.
  BOOST_FOREACH (process::name_t const& name, names)
  {
    process_t const proc = q->process_by_name(name);
    process::connections_t unresolved_connections;

    proc->configure();

    bool resolved_types = false;

    BOOST_FOREACH (process::connection_t const& data_dep_connection, data_dep_connections)
    {
      process::port_addr_t const& data_addr = data_dep_connection.first;
      process::port_addr_t const& downstream_addr = data_dep_connection.second;

      process::name_t const& data_name = data_addr.first;
      process::port_t const& data_port = data_addr.second;
      process::name_t const& downstream_name = downstream_addr.first;
      process::port_t const& downstream_port = downstream_addr.second;

      if (name == data_name)
      {
        process::port_info_t const info = proc->output_port_info(data_port);

        if (info->type == process::type_data_dependent)
        {
          throw untyped_data_dependent_exception(data_name, data_port);
        }

        resolved_types = true;

        q->connect(data_name, data_port,
                   downstream_name, downstream_port);
      }
      else
      {
        unresolved_connections.push_back(data_dep_connection);
      }
    }

    if (resolved_types)
    {
      data_dep_connections = unresolved_connections;
    }
  }
}

void
pipeline::priv
::check_for_data_dep_ports() const
{
  if (data_dep_connections.size())
  {
    static std::string const reason = "Data dependency port tracking failed";

    throw std::logic_error(reason);
  }
}

void
pipeline::priv
::propagate_pinned_types()
{
  type_pinnings_t const pinnings = type_pinnings;
  type_pinnings.clear();

  BOOST_FOREACH (type_pinning_t const& pinning, pinnings)
  {
    process::connection_t const& connection = pinning.first;
    direction_t const& direction = pinning.second;

    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;
    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    process_t const up_proc = q->process_by_name(upstream_name);
    process_t const down_proc = q->process_by_name(downstream_name);

    process::port_info_t const up_info = up_proc->output_port_info(upstream_port);
    process::port_info_t const down_info = down_proc->input_port_info(downstream_port);

    process::port_type_t const& up_type = up_info->type;
    process::port_type_t const& down_type = down_info->type;

    process::name_t name;
    process::port_t port;
    process::port_type_t type;

    switch (direction)
    {
      case push_upstream:
        if (!up_proc->set_output_port_type(upstream_port, down_type))
        {
          throw connection_dependent_type_exception(upstream_name, upstream_port,
                                                    downstream_name, downstream_port,
                                                    down_type, true);
        }

        name = upstream_name;
        port = upstream_port;
        type = down_type;

        break;
      case push_downstream:
        if (!down_proc->set_input_port_type(downstream_port, up_type))
        {
          throw connection_dependent_type_exception(upstream_name, upstream_port,
                                                    downstream_name, downstream_port,
                                                    up_type, false);
        }

        name = downstream_name;
        port = downstream_port;
        type = up_type;

        break;
      default:
        continue;
    }

    try
    {
      propagate(name);
    }
    catch (propagation_exception const& e)
    {
      throw connection_dependent_type_cascade_exception(name, port, type,
                                                        e.m_upstream_name, e.m_upstream_port,
                                                        e.m_downstream_name, e.m_downstream_port,
                                                        e.m_type, e.m_push_upstream);
    }

    // Retry the connection.
    q->connect(upstream_name, upstream_port,
               downstream_name, downstream_port);
  }

  if (type_pinnings.size())
  {
    propagate_pinned_types();
  }
}

void
pipeline::priv
::check_for_untyped_ports() const
{
  if (untyped_connections.size())
  {
    throw untyped_connection_exception();
  }
}

void
pipeline::priv
::make_connections()
{
  size_t const len = connections.size();

  for (size_t i = 0; i < len; ++i)
  {
    process::connection_t const& connection = connections[i];

    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;
    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    process_t const up_proc = q->process_by_name(upstream_name);
    process_t const down_proc = q->process_by_name(downstream_name);

    process::port_info_t const down_info = down_proc->input_port_info(downstream_port);
    process::port_flags_t const& down_flags = down_info->flags;

    config_t edge_config = config->subblock(priv::config_edge);

    // Configure the edge based on its type.
    {
      process::port_type_t const& down_type = down_info->type;
      config_t const type_config = config->subblock(priv::config_edge_type);
      config_t const edge_type_config = type_config->subblock(down_type);

      edge_config->merge_config(edge_type_config);
    }

    // Configure the edge based on what it is mapped to.
    {
      /// \todo Remember mappings.
    }

    // Configure the edge based on the connected ports.
    {
      config_t const conn_config = config->subblock(priv::config_edge_conn);
      config_t const up_config = conn_config->subblock(upstream_name + priv::port_sep + upstream_port);
      config_t const down_config = conn_config->subblock(downstream_name + priv::port_sep + downstream_port);

      edge_config->merge_config(up_config);
      edge_config->merge_config(down_config);
    }

    // Configure the edge.
    {
      process::port_flags_t::const_iterator const it = down_flags.find(process::flag_input_nodep);

      bool const has_nodep = (it != down_flags.end());

      edge_config->set_value(edge::config_dependency, (has_nodep ? "false" : "true"));
      edge_config->mark_read_only(edge::config_dependency);
    }

    edge_t const e = boost::make_shared<edge>(edge_config);

    edge_map[i] = e;

    up_proc->connect_output_port(upstream_port, e);
    down_proc->connect_input_port(downstream_port, e);

    e->set_upstream_process(up_proc);
    e->set_downstream_process(down_proc);
  }
}

void
pipeline::priv
::check_for_required_ports() const
{
  typedef std::set<process::name_t> name_set_t;
  typedef std::queue<process::name_t> name_queue_t;

  name_set_t procs;

  {
    name_queue_t to_visit;

    // Traverse the pipeline starting with a process.
    to_visit.push(process_map.begin()->first);

    // While we have processes to visit yet.
    while (!to_visit.empty())
    {
      process::name_t const cur_proc = to_visit.front();

      to_visit.pop();

      // Ignore the process if we've already visited it.
      name_set_t::const_iterator const i = procs.find(cur_proc);
      if (i != procs.end())
      {
        continue;
      }

      procs.insert(cur_proc);

      // Check for required ports.
      {
        process_t const process = q->process_by_name(cur_proc);

        // Check for required input ports.
        process::ports_t const input_ports = process->input_ports();
        BOOST_FOREACH (process::port_t const& port, input_ports)
        {
          // Check for required flags.
          process::port_flags_t const port_flags = process->input_port_info(port)->flags;

          process::port_flags_t::const_iterator const f = port_flags.find(process::flag_required);
          if (f != port_flags.end())
          {
            if (!q->input_edge_for_port(cur_proc, port))
            {
              static std::string const reason = "The input port has the required flag";

              throw missing_connection_exception(cur_proc, port, reason);
            }
          }
        }

        // Check for required output ports.
        process::ports_t const output_ports = process->output_ports();
        BOOST_FOREACH (process::port_t const& port, output_ports)
        {
          // Check for required flags.
          process::port_flags_t const port_flags = process->output_port_info(port)->flags;

          process::port_flags_t::const_iterator const f = port_flags.find(process::flag_required);
          if (f != port_flags.end())
          {
            if (q->output_edges_for_port(cur_proc, port).empty())
            {
              static std::string const reason = "The output port has the required flag";

              throw missing_connection_exception(cur_proc, port, reason);
            }
          }
        }
      }

      processes_t connected_procs;

      // Find all processes upstream of the current process.
      processes_t const upstream_procs = q->upstream_for_process(cur_proc);
      connected_procs.insert(connected_procs.end(), upstream_procs.begin(), upstream_procs.end());

      // Find all processes downstream of the current process.
      processes_t const downstream_procs = q->downstream_for_process(cur_proc);
      connected_procs.insert(connected_procs.end(), downstream_procs.begin(), downstream_procs.end());

      // Mark all connected processes for visitation.
      BOOST_FOREACH (process_t const& proc, connected_procs)
      {
        to_visit.push(proc->name());
      }
    }
  }

  if (procs.size() != process_map.size())
  {
    throw orphaned_processes_exception();
  }
}

void
pipeline::priv
::check_for_dag() const
{
  typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::directedS, process::name_t> pipeline_graph_t;
  typedef boost::graph_traits<pipeline_graph_t>::vertex_descriptor vertex_t;
  typedef std::deque<vertex_t> vertices_t;
  typedef std::map<process::name_t, vertex_t> vertex_map_t;

  pipeline_graph_t graph;

  // Create the graph.
  {
    vertex_map_t vertex_map;

    process::names_t const names = q->process_names();

    BOOST_FOREACH (process::name_t const& name, names)
    {
      vertex_t const s = boost::add_vertex(graph);
      graph[s] = name;
      vertex_map[name] = s;
    }

    BOOST_FOREACH (process::name_t const& name, names)
    {
      process_t const proc = q->process_by_name(name);
      process::ports_t const iports = proc->input_ports();

      vertex_t const t = vertex_map[name];

      BOOST_FOREACH (process::port_t const& port, iports)
      {
        process::port_addr_t const sender = q->sender_for_port(name, port);

        if (sender == process::port_addr_t())
        {
          continue;
        }

        process::name_t const& sender_name = sender.first;

        process::port_info_t const info = proc->input_port_info(port);
        process::port_flags_t const& flags = info->flags;

        process::port_flags_t::const_iterator const i = flags.find(process::flag_input_nodep);

        if (i != flags.end())
        {
          continue;
        }

        vertex_t const s = vertex_map[sender_name];

        boost::add_edge(s, t, graph);
      }
    }
  }

  vertices_t vertices;

  try
  {
    boost::topological_sort(graph, std::front_inserter(vertices));
  }
  catch (boost::not_a_dag const&)
  {
    throw not_a_dag_exception();
  }
}

void
pipeline::priv
::initialize_processes()
{
  process::names_t const names = q->process_names();

  // Initialize processes.
  BOOST_FOREACH (process::name_t const& name, names)
  {
    process_t const proc = q->process_by_name(name);

    proc->init();
  }
}

void
pipeline::priv
::check_port_frequencies() const
{
  static process::port_frequency_t const base_freq = process::port_frequency_t(1, 1);

  if (process_map.size() == 1)
  {
    process_map_t::const_iterator const i = process_map.begin();
    process_t const only_proc = i->second;

    only_proc->set_core_frequency(base_freq);

    return;
  }

  process::names_t const names = q->process_names();

  typedef std::map<process::name_t, process::port_frequency_t> process_frequency_map_t;

  process_frequency_map_t freq_map;

  std::queue<process::connection_t> unchecked_connections;

  BOOST_FOREACH (process::connection_t const& connection, connections)
  {
    unchecked_connections.push(connection);
  }

  while (!unchecked_connections.empty())
  {
    process::connection_t const connection = unchecked_connections.front();
    unchecked_connections.pop();

    process::port_addr_t const& upstream_addr = connection.first;
    process::port_addr_t const& downstream_addr = connection.second;

    process::name_t const& upstream_name = upstream_addr.first;
    process::port_t const& upstream_port = upstream_addr.second;
    process::name_t const& downstream_name = downstream_addr.first;
    process::port_t const& downstream_port = downstream_addr.second;

    process_t const up_proc = q->process_by_name(upstream_name);
    process::port_info_t const up_info = up_proc->output_port_info(upstream_port);
    process::port_frequency_t const& up_port_freq = up_info->frequency;

    process_t const down_proc = q->process_by_name(downstream_name);
    process::port_info_t const down_info = down_proc->input_port_info(downstream_port);
    process::port_frequency_t const& down_port_freq = down_info->frequency;

    if (!up_port_freq || !down_port_freq)
    {
      /// \todo Issue a warning that the edge frequency cannot be validated.

      continue;
    }

    process_frequency_map_t::const_iterator const i_up = freq_map.find(upstream_name);
    process_frequency_map_t::const_iterator const i_down = freq_map.find(downstream_name);
    process_frequency_map_t::const_iterator const i_end = freq_map.end();

    bool have_upstream = false;
    bool have_downstream = false;

    if ((i_up == i_end) &&
        (i_down == i_end))
    {
      if (!freq_map.size())
      {
        // Seed the frequency map at 1-to-1 based on the upstream process.
        freq_map[upstream_name] = base_freq;
        have_upstream = true;
      }
    }

    if (i_up != i_end)
    {
      have_upstream = true;
    }
    if (i_down != i_end)
    {
      have_downstream = true;
    }

    // Validate the connection.
    if (have_upstream && have_downstream)
    {
      process::port_frequency_t const up_proc_freq = freq_map[upstream_name];

      process::port_frequency_t const edge_freq = up_proc_freq * up_port_freq;
      process::port_frequency_t const expect_freq = edge_freq / down_port_freq;

      process::port_frequency_t const down_proc_freq = freq_map[downstream_name];

      if (down_proc_freq != expect_freq)
      {
        throw frequency_mismatch_exception(upstream_name, upstream_port, up_proc_freq,
                                           downstream_name, downstream_port, down_proc_freq);
      }
    }
    // Propagate the frequency downstream.
    else if (have_upstream)
    {
      process::port_frequency_t const up_proc_freq = freq_map[upstream_name];

      process::port_frequency_t const edge_freq = up_proc_freq * up_port_freq;
      process::port_frequency_t const expect_freq = edge_freq / down_port_freq;

      freq_map[downstream_name] = expect_freq;
    }
    // Propagate the frequency upstream.
    else if (have_downstream)
    {
      process::port_frequency_t const down_proc_freq = freq_map[downstream_name];

      process::port_frequency_t const edge_freq = down_proc_freq * down_port_freq;
      process::port_frequency_t const expect_freq = edge_freq / up_port_freq;

      freq_map[upstream_name] = expect_freq;
    }
    // Not part of the already-checked parts.
    else
    {
      unchecked_connections.push(connection);
    }
  }

  process::frequency_component_t freq_gcd = process::frequency_component_t(1);

  BOOST_FOREACH (process_frequency_map_t::value_type const& proc_freq, freq_map)
  {
    process::port_frequency_t const& freq = proc_freq.second;
    process::frequency_component_t const denom = freq.denominator();

    freq_gcd = boost::math::lcm(freq_gcd, denom);
  }

  BOOST_FOREACH (process_frequency_map_t::value_type const& proc_freq, freq_map)
  {
    process::name_t const& name = proc_freq.first;
    process::port_frequency_t const& freq = proc_freq.second;

    process::port_frequency_t const core_freq = freq_gcd * freq;

    process_t const proc = q->process_by_name(name);

    proc->set_core_frequency(core_freq);
  }
}

void
pipeline::priv
::ensure_setup() const
{
  if (!setup)
  {
    throw pipeline_not_setup_exception();
  }

  if (!setup_in_progress && !setup_successful)
  {
    throw pipeline_not_ready_exception();
  }
}

bool
pipeline::priv
::is_upstream_for(process::port_addr_t const& addr, process::connection_t const& connection)
{
  process::port_addr_t const up_addr = connection.first;

  return (addr == up_addr);
}

bool
pipeline::priv
::is_downstream_for(process::port_addr_t const& addr, process::connection_t const& connection)
{
  process::port_addr_t const down_addr = connection.second;

  return (addr == down_addr);
}

bool
pipeline::priv
::is_cluster_upstream_for(process::port_addr_t const& addr, cluster_connection_t const& cconnection)
{
  process::connection_t const connection = cconnection.first;

  return is_upstream_for(addr, connection);
}

bool
pipeline::priv
::is_cluster_downstream_for(process::port_addr_t const& addr, cluster_connection_t const& cconnection)
{
  process::connection_t const connection = cconnection.first;

  return is_downstream_for(addr, connection);
}

bool
pipeline::priv
::is_addr_on(process::name_t const& name, process::port_addr_t const& addr)
{
  process::name_t const& proc_name = addr.first;

  return (name == proc_name);
}

bool
pipeline::priv
::is_connection_with(process::name_t const& name, process::connection_t const& connection)
{
  process::port_addr_t const& upstream_addr = connection.first;
  process::port_addr_t const& downstream_addr = connection.second;

  return (is_addr_on(name, upstream_addr) || is_addr_on(name, downstream_addr));
}

bool
pipeline::priv
::is_cluster_connection_with(process::name_t const& name, cluster_connection_t const& cconnection)
{
  process::connection_t const& connection = cconnection.first;

  return is_connection_with(name, connection);
}

bool
pipeline::priv
::is_cluster_connection_for(process::connection_t const& connection, cluster_connection_t const& cconnection)
{
  process::connection_t const& cluster_connection = cconnection.first;

  return (connection == cluster_connection);
}

pipeline::priv::propagation_exception
::propagation_exception(process::name_t const& upstream_name,
                        process::port_t const& upstream_port,
                        process::name_t const& downstream_name,
                        process::port_t const& downstream_port,
                        process::port_type_t const& type,
                        bool push_upstream) throw()
  : m_upstream_name(upstream_name)
  , m_upstream_port(upstream_port)
  , m_downstream_name(downstream_name)
  , m_downstream_port(downstream_port)
  , m_type(type)
  , m_push_upstream(push_upstream)
{
  m_what = "<internal>";
}

pipeline::priv::propagation_exception
::~propagation_exception() throw()
{
}

}
