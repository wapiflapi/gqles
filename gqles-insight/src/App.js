import React, { useState } from 'react';

import { gql, ApolloClient, ApolloProvider, InMemoryCache, useQuery } from '@apollo/client';
import { ApolloLink } from 'apollo-link';
import { RetryLink } from 'apollo-link-retry';
import { HttpLink } from 'apollo-link-http';

import { loader } from 'graphql.macro';

import Avatar from '@material-ui/core/Avatar';
import Box from '@material-ui/core/Box';
import Checkbox from '@material-ui/core/Checkbox';
import ClickAwayListener from '@material-ui/core/ClickAwayListener';
import Grid from '@material-ui/core/Grid';
import IconButton from '@material-ui/core/IconButton';
import Link from '@material-ui/core/Link';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemAvatar from '@material-ui/core/ListItemAvatar';
import ListItemSecondaryAction from '@material-ui/core/ListItemSecondaryAction';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import SearchIcon from '@material-ui/icons/Search';
import Skeleton from '@material-ui/lab/Skeleton';
import SvgIcon from '@material-ui/core/SvgIcon';

import { Router, Link as RouterLink, Match as RouterMatch } from "@reach/router";

import copy from 'clipboard-copy';
import TimeAgo from 'react-timeago';
import JSONTree from 'react-json-tree';

import DelayedRender from './DelayedRender';


const client = new ApolloClient({
    cache: new InMemoryCache(),
    link: ApolloLink.from([
        new RetryLink(),
        new HttpLink({ uri: 'http://localhost:8000/graphql/' })
    ]),
});


const GetProcessApplicationNotificationsQuery = loader(
    './GetProcessApplicationNotifications.graphql');



function FriendlyTimeAgo({ date }) {
    const [friendly, setFriendly] = useState(true);

    return (friendly ? (
        <Link
          color="inherit"
          fontSize="inherit"
          onClick={() => setFriendly(!friendly)}
        >
          <TimeAgo date={date} />
        </Link>

    ) : (
        <ClickAwayListener onClickAway={() => setFriendly(!friendly)}>
          <Box component="span" fontFamily="Monospace">
            {date}
          </Box>
        </ClickAwayListener>
    ));
}




function FriendlyList({children, empty, ...props}) {
    return (
        !Array.isArray(children) || children.length ?
            <List {...props}>
              {children}
            </List>
        : <DelayedRender>
            <Box m={4}>
              {empty ||
               <Grid spacing={2} container direction="row" alignItems="center" justify="center">
                 <Grid item container xs={12} justify="center">
                   <SearchIcon fontSize="large" />
                 </Grid>
                 <Grid item>
                   There is nothing here.
                 </Grid>
               </Grid>
              }
            </Box>
          </DelayedRender>
    );
}

function Menu({ selection, setSelection }) {
    return (
        <FriendlyList
          component="nav"
          aria-label="main process applications"
          empty="Process Applications will be listed here."
        >
          {selection !== undefined ? selection.map(([key, selected], i) => (
              <ListItem
                key={`${i}-${key}`}
                button
                selected={selected}
                onClick={() => setSelection(
                    selection.map(([k, s]) => [k, k === key ? !selected : s])
                )}
              >
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={selected}
                    tabIndex={-1}
                    disableRipple
                    inputProps={{ 'aria-labelledby': `menu-label-${i}-${key}` }}
                  />
                </ListItemIcon>
                <ListItemText id={`menu-label-${i}-${key}`} primary={key} />
              </ListItem>
          )) : <DelayedRender>{[1, 2, 3].map((key) => (
              <ListItem key={key}>
                <ListItemIcon>
                  <Skeleton variant="rect" width={16}/>
                </ListItemIcon>
                <ListItemText primary={<Skeleton width="7em" />} />
              </ListItem>
          ))}</DelayedRender>}
        </FriendlyList>
    );
}

function NotificationListItem({ processApplication, notificationId, event }) {
    const [isCurrent, setIsCurrent] = useState(false);

    const idversion = (
        processApplication && event &&
            `${processApplication.name}/${event.originatorId}/${event.originatorVersion}`
    );
    const path = idversion && `/originator/${idversion}`;

    return (
        <RouterMatch path={path || "@hack-default-value"}>{({ match }) => (
            <ListItem alignItems="flex-start" selected={!!match}>
              <ListItemAvatar>{processApplication !== undefined ? (
                  <Avatar alt={processApplication.name} >
                    {processApplication.name.substring(0, 2).toUpperCase()}
                  </Avatar>
              ) : <Skeleton variant="circle" width={40} height={40} />}
              </ListItemAvatar>
              <ListItemText
                primary={event ? (
                    <Box component="span" fontFamily="Monospace">
                      {event.topic}
                    </Box>
                ) : <Skeleton width="25em"/>}
                secondary={event ? (
                    <>
                      <span style={{
                          display: 'flex',
                          alignItems: 'center'
                      }}>
                        <IconButton
                          aria-label="clipboard"
                          size="small"
                          onClick={() => copy(idversion)}
                        >
                          <SvgIcon fontSize="inherit">
                            <path d="M19 2h-4.18C14.4.84 13.3 0 12 0c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm7 18H5V4h2v3h10V4h2v16z"/>
                          </SvgIcon>
                        </IconButton>
                        <Box component="span" fontFamily="Monospace">
                          <Link
                            component={RouterLink}
                            to={path}
                            state={{event: event}}
                          >
                            {idversion}
                          </Link>
                        </Box>
                      </span>
                      <FriendlyTimeAgo date={event.timestamp} />
                    </>
                ) : <Skeleton width="25em"/>}
              />


            </ListItem>
        )}</RouterMatch>

    );
}

function Notifications({ notifications }) {
    return (
        <FriendlyList
          component="nav"
          aria-label="notifications"
          /* empty={<p>Notifications will be listed here.</p>} */
        >
          {notifications !== undefined ? notifications.edges.map((edge, i) => (
              <NotificationListItem
                key={edge.cursor}
                processApplication={edge.processApplication}
                notificationId={edge.node.notificationId}
                event={edge.node.event}
              />
          )) : <DelayedRender>{[1, 2, 3].map((key) => (
              <NotificationListItem key={key} />
          ))}</DelayedRender>}
        </FriendlyList>
    );
}

function Originator({
    location, processApplicationName, originatorId, originatorVersionString
}) {

    const event = location.state && location.state.event;
    const github = {
        scheme: "Github",
        author: "Defman21",
        base00: "#ffffff" ,
        base01: "#f5f5f5" ,
        base02: "#c8c8fa" ,
        base03: "#969896" ,
        base04: "#e8e8e8" ,
        base05: "#333333" ,
        base06: "#ffffff" ,
        base07: "#ffffff" ,
        base08: "#ed6a43" ,
        base09: "#0086b3" ,
        base0A: "#795da3" ,
        base0B: "#183691" ,
        base0C: "#183691" ,
        base0D: "#795da3" ,
        base0E: "#a71d5d" ,
        base0F: "#333333",
    };

    function loadB64JSONOrNothing(data) {
        try {
            return JSON.parse(atob(data));
        } catch (err) {
            console.log({error: err});
            return undefined;
        }
    }

    const state = event && loadB64JSONOrNothing(event.state);

    state && console.log(state);

    return (
        <Box m={4}>
          <JSONTree
            data={state}
            hideRoot={true}
            sortObjectKeys={true}
            shouldExpandNode={(keyName, data, level) => level < 2}
            theme={github}
            invertTheme={false}
          />
        </Box>
    );
}

function App() {
    const [selection, setSelection] = useState(undefined);

    const { error, data, loading } = useQuery(GetProcessApplicationNotificationsQuery, {
        pollInterval: 5000,
        onCompleted: ({ processApplications }) => {
            setSelection(processApplications.map(({ name }) => (
                // Take default values from existing selection.
                (selection || []).find(([k, s]) => k === name) || [name, false]
            )));
        },
    });

    return (
        <Grid container>
          <Grid item xs={2}>
            <Menu selection={selection} setSelection={setSelection} />
          </Grid>
          <Grid item xs={12} sm={10} md={5}>
            <Notifications
              notifications={data && data.notifications}
            />
          </Grid>
          <Grid item  xs={12} sm={10} md={5}>
            <Router>
              <Originator
                path="/originator/:processApplicationName/:originatorId/:originatorVersionString"
              />
            </Router>

          </Grid>
        </Grid>
    );
}


function AppWithProviders() {
    return (
        <ApolloProvider client={client}>
        <App />
        </ApolloProvider>
    );
}

export default AppWithProviders;
